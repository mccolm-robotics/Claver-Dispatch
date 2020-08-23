import asyncio
import ssl
import websockets
from server.users.UserManager import UserManager
from server.messages.Router import Router


class ClaverDispatch:
    def __init__(self, host: str, port: int, server_key: str=None, server_crt: str=None, client_crt: str=None) -> None:
        if server_key and server_crt and client_crt:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.load_cert_chain(server_crt, server_key)
            ssl_context.load_verify_locations(cafile=client_crt)
        else:
            ssl_context = None

        self.event_loop = asyncio.get_event_loop()
        self.clientManager = UserManager(self.event_loop)
        self.router = Router(self.clientManager, self.event_loop)
        self.start_server = websockets.serve(self.connection_handler, host, port, ssl=ssl_context) # Creates the server
        self.run()

    def run(self) -> None:
        """Starts the server"""
        server = self.event_loop.run_until_complete(self.start_server)
        try:
            print('Server: Started')
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            self.event_loop.run_until_complete(server.wait_closed())
            print('Server: Disconnected')
            self.event_loop.close()

    async def incoming_events_handler(self, websocket: websockets, path: str) -> None:
        try:
            await self.router.ingest_events(websocket, path)
        except websockets.ConnectionClosed:
            print("Incoming Event -> Stalled: Client Disconnected")

    async def outgoing_events_handler(self, websocket: websockets, path: str) -> None:
        try:
            await self.router.transmit_events(websocket, path)
        except websockets.ConnectionClosed:
            print("Outgoing Event -> Stalled: Client Disconnected")

    async def update_node_map(self) -> None:
        await self.router.broadcast_connected_users_list()

    async def connection_handler(self, websocket: websockets, path: str) -> None:
        """
        Coroutine: Websockets connection handler.
        This function executes the application logic for a single connection and closes the connection when done.
        Function parameters: it receives a WebSocket protocol instance and the URI path
        """
        # Add websocket to list of connected clients
        if self.clientManager.authenticate(websocket):
            await self.update_node_map()
            try:
                await self.router.initialize_client_state(websocket, path)
                incoming_event = asyncio.create_task(self.incoming_events_handler(websocket, path))
                outgoing_event = asyncio.create_task(self.outgoing_events_handler(websocket, path))
                done, pending = await asyncio.wait(
                    [incoming_event, outgoing_event],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
            except websockets.ConnectionClosed:
                # Exception raised when websockets.open() == False
                # Connection is closed. Exit iterator.
                pass
            finally:
                self.clientManager.detach_client(websocket)
                await self.update_node_map()

if __name__ == "__main__":
    ClaverDispatch("localhost", 6789)







"""
Resources: SSL Self-Signed Certificates

https://www.ibm.com/support/knowledgecenter/SSMNED_5.0.0/com.ibm.apic.cmc.doc/task_apionprem_gernerate_self_signed_openSSL.html
https://jamielinux.com/docs/openssl-certificate-authority/create-the-root-pair.html
https://www.electricmonk.nl/log/2018/06/02/ssl-tls-client-certificate-verification-with-python-v3-4-sslcontext/
https://stackoverflow.com/questions/33504746/doing-ssl-client-authentication-is-python
https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl
https://certbot.eff.org/docs/using.html#standalone
https://aliceh75.github.io/testing-asyncio-with-ssl *** Good ***
https://docs.python.org/3/library/ssl.html#module-ssl


Resources: WebSockets

https://websockets.readthedocs.io/en/stable/cheatsheet.html?highlight=handler#passing-additional-arguments-to-the-connection-handler
"""