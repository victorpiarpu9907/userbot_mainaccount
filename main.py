# main.py
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

from entradas import register_entradas_tasks
from salidas import register_salidas_tasks
from resumen import register_resumen_tasks
from creador_canales import register_creador_canales_tasks
from rotar_contactos import register_rotar_contactos_tasks

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_string = os.getenv("SESSION")

client = TelegramClient(StringSession(session_string), api_id, api_hash)


async def main():
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Sesión inválida o expirada")
        return

    me = await client.get_me()
    print(f"✅ Userbot activo como: {me.first_name}")

    register_entradas_tasks(client)
    register_salidas_tasks(client)
    register_resumen_tasks(client)
    register_creador_canales_tasks(client)
    register_rotar_contactos_tasks(client)

    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())