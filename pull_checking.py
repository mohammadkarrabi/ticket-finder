import pprint
import requests
import os
import time
import json

API_TOKEN = '7463830485:AAHDR-5A6ayjel9i5XzDNwUUjCiQMAk4zJg'
CHAT_IDS_FILE = 'chat_ids.txt'
valid_chat_ids = set(open(CHAT_IDS_FILE).read().splitlines())

class TicketProvider:
    def __init__(self, head_cook_addr):
        head_cook = json.load(open(head_cook_addr))
        self.headers = head_cook['headers']
        self.cookies = head_cook['cookies']
        self.base_url = 'https://ghasedak24.com/search/search_train'
    
    def check_api(self, data, callback, callback_params, update_times, user_id):
        # data = {
        #     'route': 'mashhad-tehran',
        #     'car_transport': '0',
        #     'date': '1403-03-13',
        #     'return_date': '',
        #     'count': '2',
        #     'type': '0',
        #     'coupe': '0',
        #     'filter': '0',
        # }
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
            out_message = [pprint.pformat({key2fa[key]:item[key] for key in key2fa}) for item in data_list  
                           if item['counting_en'] >= passenger_count]
            out_message = '\n'.join(out_message)
            callback_params['message'] = out_message
            callback(**callback_params)
            update_times[user_id] = str(time.time())
            print('موجود شددددددددددددددددد')
        else:

            callback_params['message'] = 'چیزی نبود!'
            # callback(**callback_params)
            print('چک شد ولی چیزی نبود:()')


def send_message(message, ch_id):

    os.environ['http_proxy'] ='http://127.0.0.1:10809'
    os.environ['https_proxy'] ='http://127.0.0.1:10809'
    headers = {
        # Already added when you pass json=
        # 'Content-Type': 'application/json',
    }
    print(message)
    json_data = {
        'chat_id': ch_id,
        'text': message
        # 'disable_notification': True,
    }

    response = requests.post(
        'https://api.telegram.org/bot' + API_TOKEN + '/sendMessage',
        headers=headers,
        json=json_data,
    )
    os.environ['http_proxy'] =''
    os.environ['https_proxy'] =''


if __name__ == '__main__':
    USER2CONFIG_ADDR = './user2config.json'
    head_cook_addr = './ghasedak_config.json'
    DELAY = 10
    update_times = {}
    user_id2config = json.load(open(USER2CONFIG_ADDR, 'r'))
    ticket_provider = TicketProvider(head_cook_addr)
    while True:
        for user_id in valid_chat_ids:
            if user_id not in update_times or user_id2config[user_id]['request_time'] > update_times[user_id]:
                config = user_id2config[user_id]
                data = config['query']
                callback_params = {"ch_id":user_id}
                ticket_provider.check_api(data, send_message, callback_params, update_times, user_id)
        time.sleep(DELAY)
        user_id2config = json.load(open(USER2CONFIG_ADDR, 'r'))
        