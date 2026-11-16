# generar_string_session.py
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 26193907      # tu api_id
api_hash = "0a78894a6867e7cb3224f42070bac614"   # tu api_hash

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("TU STRING SESSION:")
    print(client.session.save())
    
