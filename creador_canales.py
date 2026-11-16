import asyncio
import os
import re
import tempfile

from telethon import events, functions, types
from telethon.errors import FloodWaitError, RPCError
from telethon.utils import resolve_id

CREATOR_CHANNEL = -1003204309788
LOG_CHANNEL = -1003631651635

WELCOME_CREATED_TEXT = (
    "✅ Datos recibidos para crear canal:\n"
    "- Título: `{title}`\n"
    "- Visibilidad: Private\n\n"
    "Por favor sube la foto que quieres usar como avatar (en el mismo chat). "
    "Si ya la subiste, espera unos segundos."
)

BOT_IDS = [
    "@DeepSeekV4Bot",
    "@IADeepSeekBot",
    "@DeepSeekIABot",
    "@DeepSeekEspanolBot",
    "@DeepSeekPortuguesBot",
    "@DeepSeek_AppBot",
    "@DeepSeekBrasilBot",
    "@DeepSeekEnglishBot",
    "@AleixTenisBot",
    "@ReyAnalistaAdminBot",
    "@MerlwinBot",
    "@AleixFutbolBot",
    "@ZamyrRuaVIPBot",
    "@MatiasBetsContactoBot",
    "@RoiApuestasBot",
    "@DM7PremiumBot",
    "@JuanGayaBot",
    "@ChristianApuestasBot",
    "@IDAllSportsBot",
    "@ContactoPedroBot",
    "@MatiasBetsBot",
    "@JotasPicksBot",
    "@IngenieroCHATBot",
    "@ZamyrRuaaBot",
    "@ZamyrRuaaBot",
    "@ElApostadorVIPBot",
    "@SoportePedroBot",
    "@SantiTenisBot",
    "@TipsterApuestaBot",
    "@ApuestasGarciaBot",
    "@BetsAnalistas_Bot",
    "@CinthiaCossioBot"
]

pending_creation = None
created_channels = {}
seen_commands = set()

TITLE_RE = re.compile(
    r"^\s*Titulo\s*:\s*(.+?)\s*Visibilidad\s*:\s*(Private|Privada)\s*$",
    re.IGNORECASE | re.DOTALL,
)

ADD_BOTS_RE = re.compile(
    r"^\s*Canal\s*:\s*(-?\d+)\s*Bots\s*:\s*(\d+)\s*$",
    re.IGNORECASE | re.DOTALL,
)


def normalize_channel_id(marked_id: int) -> int:
    real_id, peer_type = resolve_id(marked_id)
    if peer_type.__name__ != "PeerChannel":
        return marked_id
    return real_id


async def create_private_channel(client, title: str):
    result = await client(
        functions.channels.CreateChannelRequest(
            title=title,
            about="",
            megagroup=False,
            broadcast=True,
        )
    )
    channel = result.chats[0]
    created_channels[channel.id] = channel
    return channel


async def set_channel_photo(client, channel, photo_path: str):
    uploaded = await client.upload_file(photo_path)
    await client(
        functions.channels.EditPhotoRequest(
            channel=channel,
            photo=types.InputChatUploadedPhoto(file=uploaded),
        )
    )


async def export_invite_link(client, channel) -> str:
    invite = await client(
        functions.messages.ExportChatInviteRequest(
            peer=channel
        )
    )
    return invite.link


async def handle_creation_text(event):
    global pending_creation

    text = event.raw_text or ""
    match = TITLE_RE.match(text)
    if not match:
        return False

    title = match.group(1).strip()
    visibility = match.group(2).strip().lower()

    if visibility not in ("private", "privada"):
        await event.reply("Por ahora solo está soportada la visibilidad Private.")
        return True

    pending_creation = {
        "title": title,
        "visibility": "private",
    }

    await event.reply(
        WELCOME_CREATED_TEXT.format(title=title)
    )
    return True


async def handle_creation_photo(client, event):
    global pending_creation

    if not pending_creation:
        return False

    if not event.photo:
        return False

    title = pending_creation["title"]

    fd, photo_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    try:
        downloaded = await event.download_media(file=photo_path)
        if not downloaded:
            await event.reply("No pude descargar la imagen. Inténtalo otra vez.")
            return True

        await event.reply("✅ Foto recibida. Creando canal...")

        channel = await create_private_channel(client, title)
        await set_channel_photo(client, channel, downloaded)
        invite_link = await export_invite_link(client, channel)

        await event.reply(f"✅ Canal creado con id: {channel.id}")
        await event.reply(
            f"Canal ID: `{channel.id}`\n"
            f"Invite: `{invite_link}`",
            parse_mode="md",
        )

        await event.reply(f"Canal: {channel.id}\nBots: 20")

        created_channels[channel.id] = channel
        pending_creation = None

    finally:
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception:
            pass

    return True


async def get_channel_entity(client, marked_id: int):
    real_id = normalize_channel_id(marked_id)

    if real_id in created_channels:
        return created_channels[real_id]

    try:
        return await client.get_entity(marked_id)
    except Exception:
        try:
            return await client.get_entity(real_id)
        except Exception:
            return None


async def add_bots_as_admins(client, channel_entity, amount: int):
    added = 0

    admin_rights = types.ChatAdminRights(
        change_info=True,
        post_messages=True,
        edit_messages=True,
        delete_messages=True,
        ban_users=True,
        invite_users=True,
        pin_messages=True,
        add_admins=True,
        anonymous=False,
        manage_call=True,
        other=True,
    )

    for bot_ref in BOT_IDS[:amount]:
        try:
            bot_entity = await client.get_input_entity(bot_ref)
        except Exception:
            continue

        try:
            try:
                await client(
                    functions.channels.InviteToChannelRequest(
                        channel=channel_entity,
                        users=[bot_entity],
                    )
                )
            except Exception:
                pass

            await client(
                functions.channels.EditAdminRequest(
                    channel=channel_entity,
                    user_id=bot_entity,
                    admin_rights=admin_rights,
                    rank="bot",
                )
            )

            added += 1
            await asyncio.sleep(1)

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except RPCError:
            pass
        except Exception:
            pass

    return added


async def handle_add_bots_command(client, event):
    text = event.raw_text or ""
    match = ADD_BOTS_RE.match(text)
    if not match:
        return False

    channel_id = int(match.group(1))
    amount = int(match.group(2))

    channel_entity = await get_channel_entity(client, channel_id)
    if channel_entity is None:
        await event.reply(
            "No pude resolver ese canal. Usa el ID que te devolví justo después de crearlo."
        )
        return True

    try:
        await event.reply(f"Procesando bots para el canal {channel_id}...")
        added = await add_bots_as_admins(client, channel_entity, amount)

        await event.reply(
            f"✅ Proceso terminado.\n"
            f"Canal: {channel_id}\n"
            f"Bots solicitados: {amount}\n"
            f"Bots agregados: {added}"
        )
    except Exception as e:
        await event.reply(f"Error procesando bots: {e}")

    return True


async def creator_handler(event):
    if await handle_creation_text(event):
        return

    if await handle_creation_photo(event.client, event):
        return

    if await handle_add_bots_command(event.client, event):
        return


def register_creador_canales_tasks(client):
    @client.on(events.NewMessage(chats=CREATOR_CHANNEL))
    async def _handler(event):
        await creator_handler(event)