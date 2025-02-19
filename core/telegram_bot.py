from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import telegram, os
from dotenv import load_dotenv
import asyncio
import requests
from PIL import Image
from io import StringIO , BytesIO


load_dotenv()
class TelegramBot():
    def __init__(self,token=None):
        if token:
            self.token = token
        else:
            self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot = telegram.Bot(token=self.token)
    
    async def send_message(self, chat_id, msg, image_url=None):
        chat_ids = ['-596174527']
        for chat_id in chat_ids:
            if image_url:
                res = requests.get(image_url)
                await asyncio.gather(self.bot.send_message(chat_id=chat_id, text=msg),self.bot.send_photo(chat_id=chat_id,photo= res.content))
            else:
                await asyncio.gather(self.bot.send_message(chat_id=chat_id, text=msg))

    def list_all_chats(self):
        for a in self.bot.getUpdates():
            print(a.message.chat_id)

if __name__ == "__main__":
    telegram_bot = TelegramBot()
    asyncio.run(telegram_bot.send_message(chat_id='addas',msg = "Good morning!!!!",image_url='https://sightsea-ai-space-bucket.sgp1.digitaloceanspaces.com/images/tmp/images/download%20(2)2025021900185920250219013356.png'))

