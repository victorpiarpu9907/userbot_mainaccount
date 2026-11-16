import asyncio

TARGET_CHANNEL = -1002203258867
POLL_INTERVAL = 1  # segundos

seen_events = set()


async def poll_logs_crudos(client):
    while True:
        try:
            async for event in client.iter_admin_log(TARGET_CHANNEL, limit=100):
                if event.id in seen_events:
                    continue

                seen_events.add(event.id)

                print("\n" + "=" * 80)
                print("EVENTO NUEVO DEL ADMIN LOG")
                print("=" * 80)

                try:
                    print(event.stringify())
                except Exception as e:
                    print(f"No se pudo hacer stringify del evento: {e}")
                    print(event)

                print("\n--- ORIGINAL TL OBJECT ---")
                try:
                    print(event.original.stringify())
                except Exception as e:
                    print(f"No se pudo hacer stringify del original: {e}")
                    print(event.original)

        except Exception as e:
            print(f"Error en poll_logs_crudos: {e}")

        await asyncio.sleep(POLL_INTERVAL)


def register_logs_crudos_tasks(client):
    client.loop.create_task(poll_logs_crudos(client))