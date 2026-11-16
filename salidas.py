import asyncio
import time
from collections import deque

from telethon.errors import FloodWaitError, RPCError

TARGET_CHANNEL = -1002203258867
LOG_CHANNEL = -1003631651635
SUMMARY_CHANNEL = -1004491001443

POLL_INTERVAL = 2
HOUR_SECONDS = 3600

seen_events = set()
left_timestamps = deque()
STARTED_AT = None

BYE_TEXT = (
    "👋🏻 Hola de nuevo amigo! He visto que te has salido del canal 🫠\n\n"
    "👀 Podrías darme tu opinión de por qué has tomado la decisión de salirte?\n\n"
    "😎 Me ayudaría mucho para seguir mejorando el canal. Podría volver a invitarte a entrar?\n\n"
    "💯 Un saludo crack!"
)


def trim_old_leaves(now: float | None = None) -> None:
    now = now or time.time()
    while left_timestamps and (now - left_timestamps[0]) > HOUR_SECONDS:
        left_timestamps.popleft()


def format_user(user) -> str:
    first_name = user.first_name or ""
    username = f"@{user.username}" if user.username else "sin username"
    return (
        f"First name: {first_name}\n"
        f"ID de usuario: {user.id}\n"
        f"Username: {username}"
    )


async def handle_leave(client, event):
    user = getattr(event, "user", None)

    if user is None:
        try:
            user = await client.get_entity(event.user_id)
        except Exception:
            user = None

    try:
        await client.send_message(user, BYE_TEXT)
    except Exception:
        pass

    try:
        if user is not None:
            await client.send_message(LOG_CHANNEL, "Usuario salió del canal:\n\n" + format_user(user))
        else:
            await client.send_message(LOG_CHANNEL, f"Usuario salió del canal. ID: {event.user_id}")
    except Exception:
        pass

    left_timestamps.append(time.time())
    trim_old_leaves()


async def poll_salidas(client):
    global STARTED_AT

    while True:
        try:
            async for event in client.iter_admin_log(
                TARGET_CHANNEL,
                limit=100,
                leave=True,
            ):
                if STARTED_AT is not None and event.date.timestamp() <= STARTED_AT:
                    continue

                if event.id in seen_events:
                    continue

                seen_events.add(event.id)

                if not getattr(event, "left", False):
                    continue

                try:
                    await handle_leave(client, event)
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
        trim_old_leaves()
        count_last_hour = len(left_timestamps)

        text = (
            f"📊 Resumen última hora\n\n"
            f"Usuarios que salieron: {count_last_hour}"
        )

        try:
            await client.send_message(SUMMARY_CHANNEL, text)
        except Exception:
            pass


def register_salidas_tasks(client):
    global STARTED_AT
    STARTED_AT = time.time()
    client.loop.create_task(poll_salidas(client))
    client.loop.create_task(hourly_summary_loop(client))