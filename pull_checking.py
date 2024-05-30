import logging
import colorlog
import pprint
import requests
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
logger = colorlog.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s')

file_handler = logging.FileHandler('pull.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Use the logger to create some logs

CHAT_IDS_FILE = 'chat_ids.txt'
CITY_CODE_ADDR = 'city2code.csv'
city_code_df = pd.read_csv(CITY_CODE_ADDR)
valid_chat_ids = set(open(CHAT_IDS_FILE).read().splitlines())
city2code = dict(zip(city_code_df['city'].str.lower(), city_code_df['code']))

def query2urls(query):
    route = query['route']
    source, destination = route.split('-')
    source = source.lower()
    destination = destination.lower()
    source_code = source
    destination_code = destination
    if source in city2code:
        source_code = city2code[source]
    if destination in city2code:
        destination_code = city2code[destination]
    
    date = query['date']
    alibaba_url = f'https://www.alibaba.ir/train/{source_code}-{destination_code}?departing={date}'
    ghasedak_url = f'https://ghasedak24.com/search/train/{route}/{date}'
    return [alibaba_url, ghasedak_url]


class TicketProvider:
    def __init__(self, head_cook_addr):
        head_cook = json.load(open(head_cook_addr))
        self.headers = head_cook['headers']
        self.cookies = head_cook['cookies']
        self.base_url = 'https://ghasedak24.com/search/search_train'
    
    def check_api(self, data, callback, callback_params, update_times, user_id):
        key2fa = {
            "from_title": 'از',
            "to_title": 'به',
            "jdate": 'تاریخ',
            "time": 'ساعت حرکت',
            "time_of_arrival": 'ساعت ورود',
            "wagon_name": 'نوع قطار',
            "cost_title": 'قیمت',
            "compartment_capacity": 'ظرفیت خالی'
        }
        passenger_count = int(data['count'])
        response = requests.post(f'{self.base_url}', cookies=self.cookies, headers=self.headers, data=data) 
        data_list = response.json()['data']['data']['departure']
        if any(item['counting_en'] >= passenger_count for item in data_list):
            logger.info(f'request for user id {user_id} found!!')
            out_message = [pprint.pformat({key2fa[key]:item[key] for key in key2fa}) for item in data_list  
                           if item['counting_en'] >= passenger_count]
            out_message = '\n'.join(out_message)
            callback_params['message'] = out_message
            callback(**callback_params)
            update_times[user_id] = str(time.time())
        else:
            logger.info(f'request for user id {user_id} checked by not found ')


def send_message(message, query, ch_id):
    logger.info(f'send_message() function calling for user id {ch_id} and message {message}')
    os.environ['http_proxy'] ='http://127.0.0.1:10809'
    os.environ['https_proxy'] ='http://127.0.0.1:10809'
    headers = {
        # Already added when you pass json=
        # 'Content-Type': 'application/json',
    }
    # print(message)
    urls = query2urls(query)
    urls = '\n\n'.join(urls)
    message += f'\n\nlinks: \n {urls}'
    json_data = {
        'chat_id': ch_id,
        'text': message
        # 'disable_notification': True,
    }

    response = requests.post(
        'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage',
        headers=headers,
        json=json_data,
    )
    os.environ['http_proxy'] =''
    os.environ['https_proxy'] =''


if __name__ == '__main__':
    USER2CONFIG_ADDR = './user2config.json'
    APP_CONFIG_ADDR = './app_config.json'
    head_cook_addr = './ghasedak_config.json'
    DELAY = 10
    update_times = {}
    user2log = {}
    user_id2config = json.load(open(USER2CONFIG_ADDR, 'r'))
    app_config = json.load(open(APP_CONFIG_ADDR, 'r'))
    ticket_provider = TicketProvider(head_cook_addr)
    start_time = time.time()
    duration = app_config['duration']
    while True:
        if time.time() - start_time >= duration:
            break
        for user_id in valid_chat_ids:
            if user_id not in user_id2config:
                continue
            if user_id not in update_times or user_id2config[user_id]['request_time'] > update_times[user_id]:
                config = user_id2config[user_id]
                data = config['query']
                callback_params = {"ch_id":user_id}
                callback_params['query'] = data
                ticket_provider.check_api(data, send_message, callback_params, update_times, user_id)
        time.sleep(app_config['delay'])
        user_id2config = json.load(open(USER2CONFIG_ADDR, 'r'))
        