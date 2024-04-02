import json
from bot_program import TelewebBots 
import asyncio
import os



async def main():

    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)


    bots_tasks = []
    for bot_config in config['bots']:
        bot_run = TelewebBots(**bot_config)
        bots_tasks.append(bot_run.run_bot_content())
        bots_tasks.append(bot_run.run_spam_bot())
    

    await asyncio.gather(*bots_tasks)

if __name__ == '__main__':
    asyncio.run(main())