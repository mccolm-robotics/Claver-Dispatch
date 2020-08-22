# WS client example

import asyncio
import ssl

import websockets

ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="server.crt")
ssl_context.load_cert_chain(certfile="client.crt", keyfile="client.key")

async def hello():
    uri = "ws://localhost:6789"
    async with websockets.connect(uri) as websocket:
        # name = input("What's your name? ")
        #
        # await websocket.send(name)
        # print(f"> {name}")
        while True:
            try:
                users_online = await websocket.recv()
                print(f"Online: {users_online}")
            except websockets.ConnectionClosed:
                break

try:
    asyncio.get_event_loop().run_until_complete(hello())
except KeyboardInterrupt:
    pass



