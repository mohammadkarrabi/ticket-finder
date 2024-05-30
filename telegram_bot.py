import os
import time
import json
import colorlog
import logging
from telegram.ext import Updater, MessageHandler, filters, CommandHandler
from dotenv import load_dotenv
from llm import LLMParser


logger = colorlog.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s')

file_handler = logging.FileHandler('telegram.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

os.environ['http_proxy'] ='http://127.0.0.1:10809'
os.environ['https_proxy'] ='http://127.0.0.1:10809'


# Load the environment variables from the .env file
load_dotenv()

# Get the bot token from the environment variables
USER2CONFIG_ADDR = 'user2config.json'
CHAT_IDS_ADDR = 'chat_ids.txt'
BOT_TOKEN = os.getenv('BOT_TOKEN')
llm_parser = LLMParser()
valid_chat_ids = set(list(map(str, open(CHAT_IDS_ADDR).read().splitlines())))

def is_valid_query(query_dict):
    return all(key in query_dict for key in ['count', 'route', 'date']) and '-' in query_dict['route'] and len(query_dict['date'].split('-')) == 3


def message_handler(update, context):
    logger.info(f'New message from {update.message.from_user.first_name}: {update.message.text}')
    if not str(update.effective_chat.id) in valid_chat_ids:
        context.bot.send_message(chat_id=update.effective_chat.id, text="you are not allowed to use this bot! please try another solution")
    else:
        user2config = json.load(open(USER2CONFIG_ADDR))
        try:
            resp = llm_parser.parse(update.message.text)
            logger.info(f'llm parsed response: {resp}')
            print(resp)
            query_dict = json.loads(resp)
            if not is_valid_query(query_dict):
                raise Exception
            user2config[str(update.effective_chat.id)] = {}
            user2config[str(update.effective_chat.id)]['query'] = query_dict
            user2config[str(update.effective_chat.id)]['request_time'] = str(time.time())
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"your request parsed as follow :\n {str(resp)}\n\n if its wrong try again with more clear query")
            with open(USER2CONFIG_ADDR, 'w') as f:
                json.dump(user2config, f)
        except Exception as e:
            logger.error(f'error in message handler f{str(e)}')
            context.bot.send_message(chat_id=update.effective_chat.id, text="we cant parse your query! try again please!")

def start(update, contextLLMParser):
    logger.info(f'start() for chat id : {str(update.effective_chat.id)}')
    context.bot.send_message(chat_id=update.effective_chat.id, text="send me your ticket request in Persian!")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(filters.text & (~filters.command), message_handler))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()