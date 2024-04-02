from aiogram import Bot, Dispatcher, types, F
import asyncio
import logging
from aiolimiter import AsyncLimiter
import aiosqlite
from aiogram.utils.markdown import hlink
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re, os, random
from aiofiles.os import mkdir
from aiogram.types import Message
from aiogram.types import FSInputFile
import shutil
from config import ADMIN_ID, UNWANTED_LIST
import json


class TelewebBots():

    def __init__(self, TOKEN_CONTENT: str, url_channel: str, id_channel: int, TOKEN_SPAM: str, channel_name: str, period: int, add_url_chanel: str, is_note_content: bool = False):
        """
        Конструктор для создания экземпляра контент-бота и спам-бота для телеграм-канала.

        Параметры:
            TOKEN_CONTENT (str): Токен бота для отправки контента.
            url_channel (str): URL канала для отправки контента.
            id_channel (int): ID канала для отправки контента.
            TOKEN_SPAM (str): Токен бота для рассылки спама.
            channel_name (str): Название канала для идентификации и создания директорий.
            period (int): Периодичность отправки сообщений спам-ботом (в секундах).
            add_url_channel (str): Дополнительный URL канала, если используется.
            is_note_content (bool): Нужно ли отправлять видео в кружочках
        """

        self.TOKEN_CONTENT = TOKEN_CONTENT
        self.url_channel = url_channel
        self.id_channel = id_channel
        self.TOKEN_SPAM = TOKEN_SPAM
        self.channel_name = channel_name
        self.period = period
        self.add_url_chanel = add_url_chanel
        self.is_note_content = is_note_content
        

        self.veref_message = 'Вы подали заявку в канал! Подтвердите что вы не бот.'
        self.keyboard_anwser = 'Я не бот'

        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        db_filename = f'{self.channel_name}.db'

        try:
          self.__db_path = os.path.join(f'{self.base_dir}/{self.channel_name}' , db_filename)
        except Exception:
            print('Не удалось получить атрибут пути к бд с текстом для контента.')
            pass
        
        self.limiter = AsyncLimiter(20, 1) # это нужно чтобы не привышать допуск к пропускной способности telegram api, лучше не менять


        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)


    def __str__(self):
        return f'''

        TOKEN_CONTENT - {self.TOKEN_CONTENT}\n
        url_chanel - {self.url_channel}\n
        id_chanel - {self.id_channel}\n
        TOKEN_SPAM - {self.TOKEN_SPAM}\n
        chanel_name - {self.channel_name}\n
        period - {self.period}\n
        add_url_chanel - {self.add_url_chanel}\n

        '''
    
    async def __ensure_dir(self, path_invalid, path_content):
        """
        Асинхронное создание директории, если она еще не существует.

        Параметры:
            path (str): Путь к директории, которую необходимо создать.
        """
        if not os.path.exists(path_content):
            self.bot_content_dir = await mkdir(path_content)
        elif os.path.exists(path_content):
            self.bot_content_dir = path_content


        if not os.path.exists(path_invalid):
            self.invalid_dir = await mkdir(path_invalid)
        elif os.path.exists(path_invalid):
            self.invalid_dir = path_invalid

    async def __ensure_db(self):
        """
        Асинхронное создание или подключение к базе данных канала,
        инициализация таблицы контента, если она еще не существует.
        """
        
        db_dir = os.path.join(self.base_dir, self.channel_name)
        invalid_dir = os.path.join(self.base_dir, f'{self.channel_name}_invalid')
        await self.__ensure_dir(invalid_dir, db_dir)
        db_path = os.path.join(db_dir, f"{self.channel_name}.db")
        # Инициализация или подключение к БД
        async with aiosqlite.connect(db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS content (filename TEXT, text TEXT)''')
            await db.commit()

        self.__db_path =  db_path


    async def __remove_copyright(self, text: str, unwanted_list: list) -> str:
        """
        Удаляет копирайт сообщения из постов, проходясь по тексту сообщения

        Параметры:
            text  - исходный текст сообщения
            unwanted_list - список марок, что нужно удалять из сообщения
        """
        for unwanted_pattern in unwanted_list:
            text = re.sub(unwanted_pattern, '', text, flags=re.IGNORECASE)
        return text


    async def __add_content_to_db(self, filename: str, text:str) -> None:
        """
        Добавляет контент и сообщение к нему в бд.
        
        """
        filename = os.path.basename(filename)
        try:
            print(f'Вызов скрипта добавления текста в бд. Имя файла-{filename}, текст-{text}')
            async with aiosqlite.connect(self.__db_path) as db:
                await db.execute("INSERT INTO content (filename, text) VALUES (?, ?)", (filename, text))
                await db.commit()
        except Exception as e:
            print(f"Что-то пошло не так на этапе добавления текста контента в бд: {e}")


    async def __get_and_delete_content_from_db(self, filename):
        print('Попытка получить данные из бд контента')
        attempt_db = 0
        while attempt_db < 2:
            try:
                async with aiosqlite.connect(self.__db_path) as db:
                    print(f'Вызов функции получения текста из бд. Передается - {filename}')
                    async with db.execute("SELECT text FROM content WHERE filename = ?", (filename,)) as cursor:
                        result = await cursor.fetchone()
                        if result:
                            await db.execute("DELETE FROM content WHERE filename = ?", (filename,))
                            await db.commit()
                            print(f'результат вызова извлечения текста - {result[0]}')
                            return result[0]
                        else:
                            print(f'Запись с именем файла "{filename}" не найдена.')
                            return ''
            except aiosqlite.Error as e:
                print(f'Произошла ошибка при доступе к базе данных: {e}')
                try:
                    print('попытка пересоздать бд?')
                    await self.__ensure_db()
                    attempt_db +=1
                except Exception as e:
                    print(f'Произошел совсем какой то пиздец переделывай код {e}')
                    attempt_db +=1



    async def run_spam_bot(self):
        """
        Метод запуска спам бота
        """
        
        bot = Bot(token= self.TOKEN_SPAM)
        dp = Dispatcher()


        @dp.chat_join_request()
        async def handle_chat_join_request(update: types.ChatJoinRequest):
            user_id = update.from_user.id
        
            async with self.limiter:

                try:
                    async with aiosqlite.connect("bot_users.db") as db:
                        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
                        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
                        await db.commit()
                        self.logger.info(f"Пользователь {user_id} записан в базу данных")

                except aiosqlite.Error as e:
                    self.logger.error(f"Ошибка при работе с базой данных: {e}", exc_info=True)

                except Exception as e:
                    self.logger.error(f"Непредвиденная ошибка при записи пользователя {user_id}: {e}", exc_info=True)

                # keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text= self.keyboard_anwser , url= self.add_url_chanel)]])

                # await bot.send_message(chat_id= user_id, text = self.veref_message, reply_markup=keyboard)
                # await asyncio.sleep()

                try:
                    await update.approve() 
                except Exception as e:
                    pass

                await asyncio.sleep(1) 
                await bot.send_message(chat_id= user_id, text= hlink('Вам одобрена заявка в приватный канал!', self.url_channel), parse_mode="HTML")
                await asyncio.sleep(10)
                await bot.send_message(chat_id= user_id, text= f'Также предлагаем присоеденится к нашему другому каналу! - {self.add_url_chanel}') 

        
        await dp.start_polling(bot)
  

    async def run_bot_content(self):
        bot = Bot(token= self.TOKEN_CONTENT)
        dp = Dispatcher()



        @dp.message()
        async def message_handler(msg: Message):
            if msg.from_user.id in ADMIN_ID:
                async with self.limiter:
                    try:
                        if msg.photo:

                            photo = msg.photo[-1]
                            file = await msg.bot.get_file(photo.file_id)
                            file_path = file.file_path
                            save_path = os.path.join(self.bot_content_dir, file_path.split('/')[-1])
                            mes_txt = await self.__remove_copyright(msg.caption if msg.caption else "", UNWANTED_LIST)
                            # print(f'Переданные новые файлы: {file_path} - {mes_txt}')
                            await self.__add_content_to_db(file_path, mes_txt)
                            await msg.bot.download_file(file_path, destination=save_path)
                            await msg.reply('Фото сохранено')



                        elif msg.video:

                            file = await msg.bot.get_file(msg.video.file_id )
                            file_path = file.file_path
                            save_path = os.path.join(self.bot_content_dir, file_path.split('/')[-1])
                            mes_txt = await self.__remove_copyright(msg.caption if msg.caption else "", UNWANTED_LIST)
                            # print(f'Переданные новые файлы: {file_path} - {mes_txt}')
                            await self.__add_content_to_db(file_path, mes_txt)
                            await msg.bot.download_file(file_path, destination=save_path)
                            await msg.reply('Видео сохранено')

                    except Exception as e:
                        await msg.reply(f"Фйл не может превышать 20 мгб. Не пресылайте больше 100 фотографий за раз. Ошибка - {e}")
                    

        

            else:
                msg.reply(f"У вас недостаточно прав.")



        async def move_random_file():
            """
            Рассылка файлов (видосов и фотографий)
            """

            attempt = 0                 # да это тупой сраный вонючий меркзкий костыль но мне пофег в принципе да
            while attempt < 2:          # нужен для обработки исключений когда директория есть, но доступа через атрибут класса к ней нет тк не была вызвана функция инициализации директорий и бд
                try:
                    files = [f for f in os.listdir(self.bot_content_dir) if os.path.isfile(os.path.join(self.bot_content_dir, f))]
                    video_files = [f for f in files if f.lower().endswith('.mp4')]
                    another_video_files = [f for f in files if f.lower().endswith('.mov')]
                    photo_files = [f for f in files if f.lower().endswith('.jpg')]
                    break
                except AttributeError:
                    attempt += 1
                    self.__ensure_dir()
                    print(f"Exception caught: {e}. Attempting a fix and retrying... ({attempt}/{2})")
                    if attempt >= 2:
                        print("Max attempts reached. Handling failure...")

            if not video_files and not photo_files and not another_video_files:
                print("В исходной папке нет нужных файлов.")
                return

            random_file = None
            async with self.limiter:
                try:
                    if video_files:

                        random_file = random.choice(video_files)
                        print(f'Рандом файл - {random_file}')

                        content_text = "" # просто еще один слой защиты от бесконечного цикла
                        atttempt = 0
                        while atttempt <2:
                            try:
                                content_text = await self.__get_and_delete_content_from_db(random_file)
                                break
                            except ArithmeticError:
                                atttempt+=1
                                if atttempt >= 2:
                                    print("Превышено количество попыток для video_files")

                        input_file = FSInputFile(path=os.path.join(self.bot_content_dir, random_file), filename=random_file)
                        caption = f"""{content_text}\n<a href='{self.url_channel}'>{self.channel_name}</a>"""

                        if self.is_note_content:
                            await bot.send_video_note(chat_id= self.id_channel, video_note= input_file)
                        else:
                            await bot.send_video(chat_id= self.id_channel, video=input_file, caption=caption, parse_mode='HTML')

                    elif photo_files:

                        random_file = random.choice(photo_files)
                        input_file = FSInputFile(path=os.path.join(self.bot_content_dir, random_file), filename=random_file)

                        attempt = 0  # Сброс счетчика попыток для нового блока
                        content_text = ""
                        while attempt < 2:
                            try:
                                content_text = await self.__get_and_delete_content_from_db(random_file)
                                break
                            except ArithmeticError:
                                attempt += 1
                                if attempt >= 2:
                                    print("Превышено количество попыток для получения текста для фоток")


                        caption = f"""{content_text}\n<a href='{self.url_channel}'>{self.channel_name}</a>"""
                        await bot.send_photo(chat_id=self.id_channel, photo=input_file, caption=caption, parse_mode='HTML')

                    elif another_video_files:

                        random_file = random.choice(another_video_files)
                        random_file = os.path.splitext(random_file)[0] + ".mp4"
                        
                        attempt = 0  # Сброс счетчика попыток для нового блока
                        content_text = ""
                        while attempt < 2:
                            try:
                                content_text = await self.__get_and_delete_content_from_db(random_file)
                                break
                            except ArithmeticError:
                                attempt += 1
                                if attempt >= 2:
                                    print("Превышено количество попыток для получения текста для фоток")

                        input_file = FSInputFile(path=os.path.join(self.bot_content_dir, random_file), filename=random_file)
                        caption = f"""{content_text}\n<a href='{self.url_channel}'>{self.channel_name}</a>"""
                        if self.is_note_content:
                            await bot.send_video_note(chat_id= self.id_channel, video_note= input_file)
                        else:
                            await bot.send_video(chat_id= self.id_channel, video=input_file, caption=caption, parse_mode='HTML')


                    await asyncio.sleep(5)

                except Exception as e:
                    print(f'{e}')

                finally:
                    if random_file:
                        source_file = os.path.join(self.bot_content_dir, random_file)
                        target_file = os.path.join(self.invalid_dir, random_file)
                        shutil.move(source_file, target_file)
                        print(f"Файл {random_file} был успешно перемещен из {self.bot_content_dir,} в {self.invalid_dir}")


        async def periodic_task_photos():
            while True:

                await move_random_file()  
                await asyncio.sleep(3600*self.period) 

        asyncio.create_task(periodic_task_photos())
        await self.__ensure_db()

        await dp.start_polling(bot)






# # TESTING




# async def main():

#     with open('config.json', 'r', encoding='utf-8') as file:
#         config = json.load(file)


#     bots_tasks = []
#     for bot_config in config['bots']:
#         bot_run = TelewebBots(**bot_config)
#         bots_tasks.append(bot_run.run_bot_content())
#         bots_tasks.append(bot_run.run_spam_bot())
    

#     await asyncio.gather(*bots_tasks)

# if __name__ == '__main__':
#     asyncio.run(main())