
from aiogram import Bot, Dispatcher, types, F
import logging
from aiogram.types import Message
from config import ADMIN_ID
import os
import random
from aiogram.types import FSInputFile
import asyncio
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot_content(TOKEN: str, chanel_id: int, save_floder: str, chanel_url: str, message_end_text: str):
    bot = Bot(token=TOKEN)
    dp = Dispatcher()



    @dp.message()
    async def message_handler(msg: Message):
        if msg.from_user.id in ADMIN_ID:
            try:
                if msg.photo:
                    photo = msg.photo[-1]
                    file = await msg.bot.get_file(photo.file_id)
                    file_path = file.file_path
                    save_path = os.path.join(save_floder, file_path.split('/')[-1])

                    await msg.bot.download_file(file_path, destination=save_path)
                    await msg.reply('Фото сохранено')



                elif msg.video:
                    file = await msg.bot.get_file(msg.video.file_id )
                    file_path = file.file_path
                    save_path = os.path.join(save_floder, file_path.split('/')[-1])

                    await msg.bot.download_file(file_path, destination=save_path)
                    await msg.reply('Видео сохранено')



            except Exception:
                await msg.answer(f"Фйл не может превышать 20 мгб. Не пресылайте больше 100 фотографий за раз.")


        else:
            msg.reply(f"У вас недостаточно прав.")

    async def move_random_file():
        """
        Рассылка файлов (видосов и фотографий)
        """
        target_dir = r'C:\Users\bychk\Desktop\tg_web_bot\data\invalid_c'
        files = [f for f in os.listdir(save_floder) if os.path.isfile(os.path.join(save_floder, f))]
        video_files = [f for f in files if f.endswith('.mp4')]
        photo_files = [f for f in files if f.endswith('.jpg')]

        if not video_files and not photo_files:
            print("В исходной папке нет нужных файлов.")
            return

        random_file = None
        try:
            if video_files:
                random_file = random.choice(video_files)
                input_file = FSInputFile(path=os.path.join(save_floder, random_file), filename=random_file)
                caption = f"<a href='{chanel_url}'>{message_end_text}</a>"
                await bot.send_video(chat_id=chanel_id, video=input_file, caption=caption, parse_mode='HTML')
            elif photo_files:
                random_file = random.choice(photo_files)
                input_file = FSInputFile(path=os.path.join(save_floder, random_file), filename=random_file)
                caption = f"<a href='{chanel_url}'>{message_end_text}</a>"
                await bot.send_photo(chat_id=chanel_id, photo=input_file, caption=caption, parse_mode='HTML')
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f'{e}')
        finally:
            if random_file:
                source_file = os.path.join(save_floder, random_file)
                target_file = os.path.join(target_dir, random_file)
                shutil.move(source_file, target_file)
                print(f"Файл {random_file} был успешно перемещен из {save_floder} в {target_dir}")


    async def periodic_task_photos():
        while True:

            await move_random_file()  
            await asyncio.sleep(3600) 

    asyncio.create_task(periodic_task_photos())
    await dp.start_polling(bot)


