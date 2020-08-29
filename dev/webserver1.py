# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

logging.basicConfig()

STATE = {"value": 0}

USERS = set()

COUNTID = 0

def state_event():
    return json.dumps({"type": "state", **STATE})

def users_event():
    return json.dumps({"type": "connections", "count": len(USERS)})

async def notify_state():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = state_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def notify_users():
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = users_event()
        await asyncio.wait([user.send(message) for user in USERS])

async def register(websocket):
    USERS.add(websocket)
    await notify_users()

async def unregister(websocket):
    USERS.remove(websocket)
    await notify_users()

# Synchronize application state across clients
async def counter(websocket, path):
    # register(websocket) sends user_event() to websocket
    await register(websocket)
    try:
        await websocket.send(state_event())
        async for message in websocket:
            # This is an infinite loop
            data = json.loads(message)
            if data["action"] == "minus":
                STATE["value"] -= 1
                await notify_state()
            elif data["action"] == "plus":
                STATE["value"] += 1
                await notify_state()
            else:
                logging.error("unsupported event: {}", data)
    except websockets.ConnectionClosed:
        # Exception raised when websockets.open() == False
        # Connection is closed. Do not log error.
        # Infinite loop broken
        pass
    finally:
        await unregister(websocket)

event_loop = asyncio.get_event_loop()
start_server = websockets.serve(counter, "localhost", 6789)
server = event_loop.run_until_complete(start_server)

try:
    event_loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    server.close()
    event_loop.run_until_complete(server.wait_closed())
    print('closing event loop')
    event_loop.close()
