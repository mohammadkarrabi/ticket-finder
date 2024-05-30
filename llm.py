import os
from jdatetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMParser:
    def __init__(self):
        self.model = 'gpt-4o'
        OPENAI_TOKEN = os.getenv('OPENAI_TOKEN')
        self.client = OpenAI(base_url='https://api.avalai.ir/v1', api_key=OPENAI_TOKEN)
        self.prompt_template = open('./prompt_template.txt').read()
    
    
    def get_today(self):
        now = datetime.now()
        jalali_date = now.strftime("%Y-%m-%d")
        return jalali_date

    
    def parse(self, query):
        today_date = self.get_today()
        messages = [
                {"role": "system", "content": 'you are query parser and all output must be in json format'
                },
                {"role": "user", "content": self.prompt_template.format(query=query, today_date=today_date)
                }
        ]
        response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"}
            )
        response_message = response.choices[0].message.content
        return response_message
    

if __name__ == '__main__':
    parser = LLMParser()
    print(parser.parse('۱۴ام بلیط یزد به سوادکوه'))