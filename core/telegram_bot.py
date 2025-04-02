from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import telegram, os
from dotenv import load_dotenv
import asyncio
import requests
from PIL import Image
from io import StringIO , BytesIO
from telegram.request import HTTPXRequest
import telegram
from telegram.constants import ParseMode



load_dotenv()
class TelegramBot():
    def __init__(self,token=None,parse_mode=None):
        if token:
            self.token = token
        else:
            self.token = os.getenv('TELEGRAM_AI_MEME_BOT_TOKEN')
        trequest = HTTPXRequest(connection_pool_size=20)
        self.bot = telegram.Bot(token=self.token,request=trequest)
    
    async def send_message(self, chat_id, msg, image_url=None, parse_mode=ParseMode.MARKDOWN, is_tested =True):
        if not is_tested:
            chat_ids = ['-596174527','@AIxAPE:13568','@HNNBMC','@shillchillcrew']
        else:
            chat_ids = ['-596174527']
        message_thread_id = None
        if parse_mode.lower() == 'markdown':
            parse_mode = ParseMode.MARKDOWN
        elif parse_mode.lower() == 'html':
            parse_mode = ParseMode.HTML
        else:
            parse_mode = None
        for chat_id in chat_ids:
            if ":" in chat_id:
                group_id = chat_id.split(":")[0]
                message_thread_id = chat_id.split(":")[1]
            else:
                group_id =chat_id
            if image_url:
                res = requests.get(image_url)
                await asyncio.gather(self.bot.send_message(chat_id=group_id, message_thread_id=message_thread_id,text=msg,parse_mode=parse_mode),self.bot.send_photo(chat_id=chat_id,photo= res.content))
            else:
                await asyncio.gather(self.bot.send_message(chat_id=group_id,  message_thread_id=message_thread_id,text=msg,parse_mode=parse_mode))

    async def list_all_chats(self):
        info = await self.bot.getUpdates() 
        me = await self.bot.getMe()
        for a in info:
            print(a.message.chat_id)
    
if __name__ == "__main__":
    telegram_bot = TelegramBot()
    asyncio.run(telegram_bot.list_all_chats())
    #asyncio.run(telegram_bot.send_message(chat_id='addas',msg = "Hi there!!!!",image_url='https://sightsea-ai-space-bucket.sgp1.digitaloceanspaces.com/images/tmp/images/download%20(2)2025021900185920250219013356.png'))

