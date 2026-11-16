import asyncio
import random

from telethon import events, functions
from telethon.errors import FloodWaitError, RPCError

ROTATE_CHANNEL = -1003887538898  # cambia esto por el ID real

CONTACT_IDS = [
    6063172769,
    5085590486,
    1164415631,
    8652683565,
    7994243740,
    1068957036,
]

MALE_NAMES = ['Juan', 'José', 'Luis', 'Carlos', 'Jorge', 'Miguel', 'Pedro', 'Andrés', 'Ricardo', 'Santiago', 'Javier', 'Fernando', 'Manuel', 'Alejandro', 'Daniel', 'Diego', 'Eduardo', 'Óscar', 'Pablo', 'Rafael', 'Hugo', 'Alberto', 'Emilio', 'Roberto', 'Raúl', 'Francisco', 'Gerardo', 'Víctor', 'Héctor', 'Iván', 'Sergio', 'Mauricio', 'Marcos', 'Ángel', 'Arturo', 'Enrique', 'Cristian', 'Tomás', 'Gustavo', 'Ramiro', 'Benjamín', 'Salvador', 'Simón', 'Omar', 'Lucas', 'Nicolás', 'Esteban', 'Kevin', 'Bruno', 'Ariel', 'Samuel', 'Fabio', 'Rubén', 'Joel', 'César', 'Edgar', 'Julián', 'Adrián', 'Fabián', 'Damián', 'Leonardo', 'René', 'Hernán', 'Nelson', 'Emmanuel', 'Patricio', 'Milton', 'Ciro', 'Elías', 'Noé', 'Mateo', 'Thiago', 'Gael', 'Braulio', 'Osvaldo', 'Néstor', 'Eugenio', 'Aarón', 'Lorenzo', 'Israel', 'Rodrigo', 'Agustín', 'Darío', 'Cristóbal', 'Maximiliano', 'Iker', 'Alan', 'Camilo', 'Humberto', 'Felipe', 'Tadeo', 'Rómulo', 'Ezequiel', 'Aurelio', 'Jairo', 'Marco', 'Ulises', 'Tobías', 'Valentín', 'Adolfo']
FEMALE_NAMES = ['María', 'Ana', 'Laura', 'Sofía', 'Valentina', 'Camila', 'Daniela', 'Andrea', 'Paula', 'Carolina', 'Fernanda', 'Gabriela', 'Adriana', 'Diana', 'Patricia', 'Luisa', 'Marta', 'Verónica', 'Natalia', 'Mariana', 'Claudia', 'Elena', 'Rosa', 'Dora', 'Angela', 'Ángela', 'Lorena', 'Cecilia', 'Mónica', 'Yolanda', 'Liliana', 'Karla', 'Catalina', 'Ivonne', 'Martha', 'Nadia', 'Paola', 'Jimena', 'Ximena', 'Silvia', 'Tatiana', 'Alejandra', 'Beatriz', 'Inés', 'Sara', 'Julia', 'Teresa', 'Rocío', 'Lina', 'Lucía', 'Noelia', 'Alicia', 'Bárbara', 'Cristina', 'Evelyn', 'Gina', 'Helena', 'Irene', 'Jazmín', 'Katherine', 'Leidy', 'Manuela', 'Melissa', 'Nora', 'Olga', 'Paty', 'Rebeca', 'Sabrina', 'Tamara', 'Úrsula', 'Vicky', 'Wendy', 'Yasmin', 'Zaira', 'Abigail', 'Brenda', 'Cinthia', 'Denisse', 'Esperanza', 'Fabiola', 'Graciela', 'Hilda', 'Itzel', 'Jaqueline', 'Karen', 'Luz', 'Mireya', 'Nancy', 'Ofelia', 'Pilar', 'Ruth', 'Susana', 'Tania', 'Viviana', 'Xiomara', 'Yessica', 'Zulema', 'Amalia', 'Atenea', 'Dafne']
SURNAMES = ['García', 'Rodríguez', 'González', 'Hernández', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Díaz', 'Torres', 'Ramírez', 'Flores', 'Vargas', 'Castro', 'Rojas', 'Morales', 'Ortiz', 'Ruiz', 'Jiménez', 'Mendoza', 'Reyes', 'Cruz', 'Moreno', 'Álvarez', 'Romero', 'Herrera', 'Medina', 'Aguilar', 'Guerrero', 'Cortés', 'Núñez', 'León', 'Ramos', 'Vásquez', 'Chávez', 'Salazar', 'Fuentes', 'Carrillo', 'Soto', 'Molina', 'Suárez', 'Delgado', 'Pacheco', 'Campos', 'Peña', 'Navarro', 'Ibarra', 'Arias', 'Escobar', 'Ortega', 'Silva', 'Valencia', 'Correa', 'Ospina', 'Duque', 'Gutiérrez', 'Hincapié', 'Cárdenas', 'Montoya', 'Restrepo', 'Cardona', 'Cano', 'Alvarado', 'Castaño', 'Rincón', 'Bermúdez', 'Buitrago', 'Pineda', 'Patiño', 'Arango', 'Robledo', 'Londoño', 'Jaramillo', 'Quintero', 'Uribe', 'Tobón', 'Acuña', 'Bello', 'Beltrán', 'Sierra', 'Mejía', 'Castañeda', 'Pardo', 'Calle', 'Bonilla', 'Vega', 'Cabrera', 'Orozco', 'Zapata', 'Fajardo', 'Mesa', 'Trujillo', 'Rueda', 'Barrera', 'Pinzón', 'Peñaloza', 'Serrano', 'Lozano', 'Márquez']

RUNNING = False


def build_assignments(contact_ids):
    if len(contact_ids) < 2:
        raise ValueError("Debes definir al menos 2 contactos.")

    main_ids = contact_ids[:-2]
    reserved_ids = contact_ids[-2:]

    full_name_count = random.randint(0, len(main_ids))
    full_name_positions = set(random.sample(range(len(main_ids)), k=full_name_count)) if main_ids else set()

    assignments = []

    for idx, user_id in enumerate(main_ids):
        first_name = random.choice(MALE_NAMES)
        last_name = random.choice(SURNAMES) if idx in full_name_positions else ""
        assignments.append((user_id, first_name, last_name))

    for user_id in reserved_ids:
        assignments.append((user_id, random.choice(FEMALE_NAMES), ""))

    return assignments


async def delete_contacts(client, user_ids):
    input_users = []
    for user_id in user_ids:
        try:
            input_users.append(await client.get_input_entity(user_id))
        except Exception:
            pass

    if not input_users:
        return

    await client(
        functions.contacts.DeleteContactsRequest(
            id=input_users
        )
    )


async def add_contact(client, user_id, first_name, last_name):
    user = await client.get_entity(user_id)

    await client(
        functions.contacts.AddContactRequest(
            id=await client.get_input_entity(user_id),
            first_name=first_name,
            last_name=last_name,
            phone=""
        )
    )

    return user


async def rotate_contacts(client):
    assignments = build_assignments(CONTACT_IDS)

    await delete_contacts(client, CONTACT_IDS)
    await asyncio.sleep(2)

    summary_lines = []

    for i, (user_id, first_name, last_name) in enumerate(assignments, start=1):
        try:
            user = await add_contact(client, user_id, first_name, last_name)

            pretty_name = (first_name + " " + last_name).strip()
            username = f"@{user.username}" if getattr(user, "username", None) else "sin username"

            line = f"[{i}/{len(assignments)}] {username} {user_id} -> {pretty_name}"
            summary_lines.append(line)

            await asyncio.sleep(1)

        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except RPCError:
            pass
        except Exception:
            pass

    if summary_lines:
        summary_text = "✅ Resumen de rotación de contactos:\n\n" + "\n".join(summary_lines)
        await client.send_message(ROTATE_CHANNEL, summary_text[:4000])


def register_rotar_contactos_tasks(client):
    @client.on(events.NewMessage(chats=ROTATE_CHANNEL, outgoing=True, pattern=r"(?i)^rotar$"))
    async def handler(event):
        global RUNNING

        if RUNNING:
            await event.reply("Ya hay una rotación en curso.")
            return

        RUNNING = True
        try:
            await event.reply("✅ Iniciando rotación de contactos...")
            await rotate_contacts(event.client)
            await event.reply("✅ Rotación terminada.")
        finally:
            RUNNING = False