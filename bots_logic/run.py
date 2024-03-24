import asyncio
from bot_hard import run_bot_hard
from bot_content import run_bot_content

from config import (
    BOT_TOKEN_HARD_SPAM, URL_HARD, 
    BOT_TOKEN_ONLYF_SPAM, URL_ONLYF, 
    BOT_TOKEN_HENT_SPAM, URL_HENT, 
    BOT_TOKEN_HOME_SPAM,  URL_HOME
)
from config import (
    BOT_TOKEN_HARD, CHANNEL_ID_HARD, SAVE_FOLDER_HARD, 
    BOT_TOKEN_HENT, CHANNEL_ID_HENT, SAVE_FOLDER_HENT,
    BOT_TOKEN_HOME, CHANNEL_ID_HOME, SAVE_FOLDER_HOME, 
    BOT_TOKEN_ONLYF, CHANNEL_ID_ONLYF, SAVE_FOLDER_ONLYF,                                                                   # привет артем из будущего
)                                                                                                                           # Я знаю это пиздец и что в этом разобраться невозможно    
                                                                                                                            # Но я рад что оно запустилось       
bot_content_info = [
            (BOT_TOKEN_HARD, CHANNEL_ID_HARD, SAVE_FOLDER_HARD, URL_HARD, 'РЕАЛЬНАЯ ЗАПРЕЩЕНКА.'      ),
            (BOT_TOKEN_HENT, CHANNEL_ID_HENT, SAVE_FOLDER_HENT, URL_HENT, 'HENTACHI'     ),
            (BOT_TOKEN_HOME, CHANNEL_ID_HOME, SAVE_FOLDER_HOME, URL_HOME, 'Милфа Виктория'      ),
            (BOT_TOKEN_ONLYF, CHANNEL_ID_ONLYF, SAVE_FOLDER_ONLYF, URL_ONLYF, 'СЛИВЫ ОНЛИФАНС'  )
]

bots_spam_info = [
             (BOT_TOKEN_HARD_SPAM,  "Привет! Вы подали заявку в секретный канал. Подтвердите что вы не бот.", URL_ONLYF, "Я не бот"), 
             (BOT_TOKEN_ONLYF_SPAM, "Привет! Вы подали заявку в секретный канал. Подтвердите что вы не бот.", URL_HENT, "Я не бот"), 
             (BOT_TOKEN_HENT_SPAM,  "Привет! Вы подали заявку в секретный канал. Подтвердите что вы не бот.", URL_HOME, "Я не бот"), 
             (BOT_TOKEN_HOME_SPAM,  "Привет! Вы подали заявку в секретный канал. Подтвердите что вы не бот.", URL_HARD ,"Я не бот"), 
                ]


async def main():

    tasks = [run_bot_hard(token, welcome_text, url, msg_txt) for token, welcome_text, url, msg_txt in bots_spam_info]
    tasks += [run_bot_content(token, chanel_id, save_folder, chanel_url, message_end_text) for token, chanel_id, save_folder, chanel_url, message_end_text in bot_content_info]
    
    await asyncio.gather(*tasks)
    
if __name__ == '__main__':
    print('working...')
    asyncio.run(main())