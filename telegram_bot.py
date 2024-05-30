import os
import time
import json
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from dotenv import load_dotenv
from llm import LLMParser


os.environ['http_proxy'] ='http://127.0.0.1:10809'
os.environ['https_proxy'] ='http://127.0.0.1:10809'


# Load the environment variables from the .env file
load_dotenv()

# Get the bot token from the environment variables
USER2CONFIG_ADDR = 'user2config.json'
BOT_TOKEN = os.getenv('BOT_TOKEN')
llm_parser = LLMParser()



def is_valid_query(query_dict):
    return all(key in query_dict for key in ['count', 'route', 'date']) and '-' in query_dict['route'] and len(query_dict['date'].split('-')) == 3


def message_handler(update, context):
    user2config = json.load(open(USER2CONFIG_ADDR))
    try:
        resp = llm_parser.parse(update.message.text)
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
        print(str(e))
        context.bot.send_message(chat_id=update.effective_chat.id, text="we cant parse your query! try again please!")
    print(f'New message from {update.message.from_user.first_name}: {update.message.text}')

def start(update, contextLLMParser):
    context.bot.send_message(chat_id=update.effective_chat.id, text="send me your ticket request in Persian!")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()