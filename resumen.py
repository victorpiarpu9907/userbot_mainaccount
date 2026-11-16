import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone


from telethon.errors import FloodWaitError, RPCError

TARGET_CHANNEL = -1002203258867
LOG_CHANNEL = -1003631651635

GRACIAS_TEXT = (
    "💪🏻 Gracias por ser parte de nuestra comunidad! "
    "Cualquier duda estamos atentos a resolverla 🥸"
)

BYE_TEXT = "🙂 Hasta pronto amigo, te extrañaremos. Aunque si quieres volver a unirte, te damos nuevamente la bienvenida a nuestra comunidad! 👋🏻"
TZ = timezone(timedelta(hours=-5))  # Colombia

RUN_HOUR = 10
RUN_MINUTE = 0

ENTRY_ACTIONS = {
    "ChannelAdminLogEventActionParticipantJoinByInvite",
    "ChannelAdminLogEventActionParticipantJoinByRequest",
}

LEAVE_ACTIONS = {
    "ChannelAdminLogEventActionParticipantLeave",
}

SLEEP_BETWEEN_DM = 5
seen_runs = set()


def format_user(user) -> str:
    first_name = user.first_name or ""
    username = f"@{user.username}" if user.username else "sin username"
    return (
        f"First name: {first_name}\n"
        f"ID de usuario: {user.id}\n"
        f"Username: {username}"
    )


async def resolve_user(client, user_id):
    try:
        return await client.get_entity(user_id)
    except Exception:
        return None


async def collect_last_24h_events(client):
    cutoff = datetime.now(TZ) - timedelta(hours=24)
    events = []

    async for event in client.iter_admin_log(
        TARGET_CHANNEL,
        limit=None,
        join=True,
        leave=True,
        invite=True,
    ):
        # iter_admin_log va de más reciente a más antiguo.
        if event.date < cutoff:
            break

        action_name = type(event.action).__name__

        if action_name in ENTRY_ACTIONS:
            kind = "enter"
        elif action_name in LEAVE_ACTIONS:
            kind = "leave"
        else:
            continue

        events.append(
            {
                "event_id": event.id,
                "date": event.date,
                "user_id": event.user_id,
                "kind": kind,
                "action_name": action_name,
            }
        )

    return events


async def get_current_member_ids(client):
    current_ids = set()
    async for user in client.iter_participants(TARGET_CHANNEL, limit=None):
        current_ids.add(user.id)
    return current_ids


def build_user_activity(events):
    """
    Devuelve:
      - entered_ids: ids que entraron alguna vez en la ventana
      - left_ids: ids que salieron alguna vez en la ventana
      - rejoined_ids: ids que salieron y luego volvieron a entrar
    """
    entered_ids = set()
    left_ids = set()

    latest_action_by_user = {}
    saw_enter = defaultdict(bool)
    saw_leave = defaultdict(bool)

    # events viene en orden más reciente -> más antiguo
    for ev in events:
        uid = ev["user_id"]
        kind = ev["kind"]

        if kind == "enter":
            entered_ids.add(uid)
            saw_enter[uid] = True
        elif kind == "leave":
            left_ids.add(uid)
            saw_leave[uid] = True

        # La primera vez que vemos al usuario es su acción más reciente
        if uid not in latest_action_by_user:
            latest_action_by_user[uid] = kind

    rejoined_ids = set()
    for uid in entered_ids & left_ids:
        # Si la acción más reciente es enter y también hubo leave,
        # interpretamos que salió y luego volvió a entrar.
        if latest_action_by_user.get(uid) == "enter":
            rejoined_ids.add(uid)

    return entered_ids, left_ids, rejoined_ids


async def send_dm_with_delay(client, user, text):
    try:
        await client.send_message(user, text)
    except Exception:
        pass
    await asyncio.sleep(SLEEP_BETWEEN_DM)


async def run_summary(client):
    events = await collect_last_24h_events(client)
    current_ids = await get_current_member_ids(client)

    entered_ids, left_ids, rejoined_ids = build_user_activity(events)

    # Entraron y siguen dentro
    active_entered_ids = [uid for uid in entered_ids if uid in current_ids]

    # Salieron y definitivamente ya no están
    departed_ids = [uid for uid in left_ids if uid not in current_ids]

    # Salieron y luego volvieron
    rejoined_ids = [uid for uid in rejoined_ids if uid in current_ids]

    # Enviar gracias a quienes siguen dentro
    thanked = []
    for uid in active_entered_ids:
        user = await resolve_user(client, uid)
        if user is None:
            continue
        await send_dm_with_delay(client, user, GRACIAS_TEXT)
        thanked.append(user)

    # Enviar despedida a quienes ya no están
    said_bye = []
    for uid in departed_ids:
        user = await resolve_user(client, uid)
        if user is None:
            continue
        await send_dm_with_delay(client, user, BYE_TEXT)
        said_bye.append(user)

    # Preparar resumen para logs
    lines = []
    lines.append("📊 Resumen diario últimas 24 horas\n")
    lines.append(f"Entraron: {len(entered_ids)}")
    lines.append(f"Salieron: {len(left_ids)}")
    lines.append(f"Salieron y volvieron a entrar: {len(rejoined_ids)}")
    lines.append(f"Siguen dentro: {len(active_entered_ids)}")
    lines.append(f"Ya no están: {len(departed_ids)}\n")

    if active_entered_ids:
        lines.append("✅ Siguen dentro:")
        for uid in active_entered_ids:
            user = await resolve_user(client, uid)
            if user:
                lines.append(f"- {format_user(user)}")
            else:
                lines.append(f"- ID de usuario: {uid}")
        lines.append("")

    if departed_ids:
        lines.append("❌ Ya no están:")
        for uid in departed_ids:
            user = await resolve_user(client, uid)
            if user:
                lines.append(f"- {format_user(user)}")
            else:
                lines.append(f"- ID de usuario: {uid}")
        lines.append("")

    if rejoined_ids:
        lines.append("🔁 Salieron y volvieron a entrar:")
        for uid in rejoined_ids:
            user = await resolve_user(client, uid)
            if user:
                lines.append(f"- {format_user(user)}")
            else:
                lines.append(f"- ID de usuario: {uid}")

    summary_text = "\n".join(lines)

    try:
        await client.send_message(LOG_CHANNEL, summary_text[:4000])
    except Exception as e:
        print(f"Error enviando resumen al canal de logs: {e}")

    print(summary_text)


async def scheduler_loop(client):
    while True:
        now = datetime.now(TZ)
        next_run = now.replace(hour=RUN_HOUR, minute=RUN_MINUTE, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run + timedelta(days=1)

        sleep_seconds = (next_run - now).total_seconds()
        print(f"Próximo resumen: {next_run.isoformat()}")
        await asyncio.sleep(sleep_seconds)

        run_key = next_run.date().isoformat()
        if run_key in seen_runs:
            continue

        seen_runs.add(run_key)

        try:
            await run_summary(client)
        except FloodWaitError as e:
            print(f"FloodWait en resumen: dormir {e.seconds} segundos")
            await asyncio.sleep(e.seconds)
        except RPCError as e:
            print(f"Error de Telegram en resumen: {e}")
        except Exception as e:
            print(f"Error inesperado en resumen: {e}")


def register_resumen_tasks(client):
    client.loop.create_task(scheduler_loop(client))