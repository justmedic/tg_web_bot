from aiogram import Bot, Dispatcher, types, F
import asyncio
import logging
import aiosqlite
from aiogram.utils.markdown import hlink
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot_hard(TOKEN: str, b_text: str, b_url: str, msg_txt: str):
    bot = Bot(token=TOKEN)
    dp = Dispatcher()


    @dp.chat_join_request()
    async def handle_chat_join_request(update: types.ChatJoinRequest):
        user_id = update.from_user.id
        
        try:
            async with aiosqlite.connect("bot_users.db") as db:
                await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
                await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
                await db.commit()
                logger.info(f"Пользователь {user_id} записан в базу данных")
        except aiosqlite.Error as e:
            logger.error(f"Ошибка при работе с базой данных: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при записи пользователя {user_id}: {e}", exc_info=True)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text= b_text, url= b_url)]])

        await bot.send_message(chat_id= user_id, text = msg_txt, reply_markup=keyboard)
        await asyncio.sleep(10)
        try:
            await update.approve() 
        except Exception as e:
            pass
        await bot.send_message(chat_id= user_id, text= hlink('Вам одобрена заявка в приватный канал!', b_url))

    
    await dp.start_polling(bot)
