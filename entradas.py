import asyncio
import time
from collections import deque

from telethon.errors import FloodWaitError, RPCError

TARGET_CHANNEL = -1002203258867
LOG_CHANNEL = -1003631651635
SUMMARY_CHANNEL = -1004491001443

WELCOME_TEXT = (
    "👋🏻 Hola! Ya te he aceptado en mi canal 👌🏻\n\n"
    "❗️Cualquier duda que puedas tener solo avísame 👀 Estaré atento para ayudarte a Generar dinero con las apuestas deportivas\n\n"
    "✅Este es mi chat privado me puedes escribir por aquí cualquier consulta 🔥"
)

WELCOME_TEXT2 = "❓Has apostado alguna vez? "

POLL_INTERVAL = 2
HOUR_SECONDS = 3600

ENTRY_ACTIONS = {
    "ChannelAdminLogEventActionParticipantJoinByInvite",
    "ChannelAdminLogEventActionParticipantJoinByRequest",
}

seen_events = set()
accepted_timestamps = deque()
STARTED_AT = None


def trim_old_approvals(now: float | None = None) -> None:
    now = now or time.time()
    while accepted_timestamps and (now - accepted_timestamps[0]) > HOUR_SECONDS:
        accepted_timestamps.popleft()


def format_user(user) -> str:
    first_name = user.first_name or ""
    username = f"@{user.username}" if user.username else "sin username"
    return (
        f"First name: {first_name}\n"
        f"ID de usuario: {user.id}\n"
        f"Username: {username}"
    )


async def handle_join(client, event):
    user = getattr(event, "user", None)
    if user is None:
        return

    try:
        await client.send_message(user, WELCOME_TEXT)
        await client.send_message(user, WELCOME_TEXT2)
    except Exception:
        pass

    try:
        await client.send_message(LOG_CHANNEL, format_user(user))
    except Exception:
        pass

    accepted_timestamps.append(time.time())
    trim_old_approvals()


async def poll_entradas(client):
    global STARTED_AT

    while True:
        try:
            async for event in client.iter_admin_log(
                TARGET_CHANNEL,
                limit=100,
                join=True,
                invite=True,
            ):
                if STARTED_AT is not None and event.date.timestamp() <= STARTED_AT:
                    continue

                if event.id in seen_events:
                    continue

                seen_events.add(event.id)

                action_name = type(event.action).__name__
                if action_name not in ENTRY_ACTIONS:
                    continue

                try:
                    await handle_join(client, event)
                    await asyncio.sleep(2)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except RPCError:
                    pass
                except Exception:
                    pass

        except Exception:
            pass

        await asyncio.sleep(POLL_INTERVAL)


async def hourly_summary_loop(client):
    while True:
        await asyncio.sleep(HOUR_SECONDS)
        trim_old_approvals()
        count_last_hour = len(accepted_timestamps)

        text = (
            f"📊 Resumen última hora\n\n"
            f"Solicitudes aceptadas: {count_last_hour}"
        )

        try:
            await client.send_message(SUMMARY_CHANNEL, text)
        except Exception:
            pass


def register_entradas_tasks(client):
    global STARTED_AT
    STARTED_AT = time.time()
    client.loop.create_task(poll_entradas(client))
    client.loop.create_task(hourly_summary_loop(client))