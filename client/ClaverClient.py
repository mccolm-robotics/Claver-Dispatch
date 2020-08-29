import asyncio
import json
import ssl
import websockets

class ClaverClient:
    def __init__(self, use_ssl=False):
        if use_ssl:
            self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile="server.crt")
            self.ssl_context.load_cert_chain(certfile="client.crt", keyfile="client.key")
        self.uri = "ws://localhost:6789"
        self.secret_key = "2fa9acf0a0fa4960834dccdb7053f8b5"
        self.serial_num = "000000003d1d1c36"
        self.credentials = json.dumps({"agent": "node", "nid": self.serial_num, "token": "958058", "qdot": "f0a0fa4960834dcc"})
        self.run()

    async def connection_handler(self):
        access_granted = False
        async with websockets.connect(self.uri) as websocket:
            while True:
                try:
                    if not access_granted:
                        await websocket.send(self.credentials)
                        response = await websocket.recv()
                        if response == "granted":
                            access_granted = True
                            print("access granted")
                    else:
                        users_online = await websocket.recv()
                        print(f"Client: {users_online}")
                except websockets.ConnectionClosed:
                    break

    def run(self):
        try:
            asyncio.get_event_loop().run_until_complete(self.connection_handler())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    ClaverClient(use_ssl=False)

