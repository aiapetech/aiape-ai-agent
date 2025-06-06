import os
import sys
sys.path.append(os.getcwd())
from telethon import TelegramClient, events
# from kafka import KafkaProducer
import json
from core.telegram_bot import TelegramBot
os.environ['PYTHONASYNCIODEBUG'] = '1'
import asyncio


# Get API credentials from env
api_id = 25666105

api_hash = "ac0631ffdfaad537877ab222e0c2512c"
# kafka_topic = os.environ.get('KAFKA_TOPIC', 'telegram-messages')
# kafka_bootstrap = os.environ.get('KAFKA_BOOTSTRAP', 'localhost:9092')

# Set up Telegram client
client = TelegramClient('sesssion_2', api_id, api_hash)
pass
# Set up Kafka producer
# producer = KafkaProducer(
#     bootstrap_servers=[kafka_bootstrap],
#     value_serializer=lambda v: json.dumps(v).encode('utf-8')
# )
# CHANNELS ={
#     "MemesNotFound": "DegenSeals",
#     "WAGMIMemesHub": "spydefi",
#     "MemechiDAO": "justsomecalls",
#     "SHILLuminatiSS": "eezzyjournal",
#     "WAGMICult_0x": "sadcatgamble",
#     "MemeGenProtocol": "watisdes",
#     "TheShillArea51": "chiggajogambles",
#     "ShillverineX": "ArcaneGems",
#     "BoneFiShillers": "MultiChain1000x",
#     "GhostShillSocietySS": "ryoshigamble",
#     "MemesNotFound":"-1002344214917"
# }
CHANNELS = {
    "DegenSeals": "@MemesNotFound",
    "spydefi": "@WAGMIMemesHub",
    "justsomecalls": "@MemechiDAO",
    "eezzyjournal": "@SHILLuminatiSS",
    "sadcatgamble": "@WAGMICult_0x",
    "watisdes": "@MemeGenProtocol",
    "chiggajogambles": "@TheShillArea51",
    "ArcaneGems": "@ShillverineX",
    "MultiChain1000x": "@BoneFiShillers",
    "ryoshigamble": "@GhostShillSocietySS",
    "-1002344214917":"@TheShillArea51",
}
listen_channels = []
for channel in CHANNELS.keys():
    if channel.startswith('-'):
        listen_channels.append(int(channel))
    else:
        listen_channels.append(channel)
async def send_message_to_group(channel, message):
    await client.send_message(entity=channel, message=message)

async def get_channel_permissions(channel):
    me = await client.get_me()
    permissions = await client.get_permissions(entity=channel,user=me)
    return me, permissions

@client.on(events.NewMessage(chats=listen_channels))
async def handler(event):
    sender = await event.get_sender()
    message = {
        'sender': sender.username or sender.id,
        'text': event.raw_text
    }
    sended_channel_id = event.chat.id
    for key, value in CHANNELS.items():
        if (str(sended_channel_id) in key.lower()) or ((event.chat.username is not None) and (key.lower() in event.chat.username.lower())):
            if value.startswith('-'):
                received_channel = int(value)
            else:
                received_channel = value
            break
    print(message)
    await send_message_to_group(channel=received_channel, message=event.raw_text)

async def main():
    await client.start()
    me, permissions = await get_channel_permissions(channel="@TheShillArea51")
    print(me)
    print(permissions)
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())