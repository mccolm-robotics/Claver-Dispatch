import asyncio
import ssl

import websockets
from server.connections.ConnectionManager import ConnectionManager
from server.messages.Router import Router

class BadCredentials(Exception):
    def __init__(self, ip_address):
        self.ip_address = ip_address

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
        # self.event_loop.set_debug(True)     # Turn on debug mode
        self.event_loop.run_until_complete(self.initialize_members())
        self.start_server = websockets.serve(self.connection_handler, host, port, ssl=ssl_context) # Creates the server
        self.run()

    async def initialize_members(self):
        self.connectionManager = await ConnectionManager.initialize(self.event_loop)
        self.router = Router(self.connectionManager, self.event_loop)

    def run(self) -> None:
        """Starts the server. Initiates the websocket connection. """
        server = self.event_loop.run_until_complete(self.start_server)  # Specifies the connection coroutine
        try:
            print('Server: Started')
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.event_loop.run_until_complete(self.connectionManager.cleanup())    # run_until_complete turns an async call into a blocking synchronous call
            server.close()
            self.event_loop.run_until_complete(server.wait_closed())
            print('Server: Disconnected')
            # self.event_loop.stop()  # Changing loop.close() to loop.stop() prevents an exception when there are still running tasks.
            self.event_loop.run_until_complete(self.event_loop.shutdown_asyncgens())
            self.event_loop.close()


    async def connection_handler(self, websocket: websockets, path: str):
        """
        Coroutine: Websockets connection handler.
        This function executes the application logic for a single connection and closes the connection when done.
        Function parameters: it receives a WebSocket protocol instance and the URI path
        """

        try:
            print("Client Connected:")
            async for message in websocket:
                if self.connectionManager.is_authorized_user(websocket):    # Has the connection been registered?
                    await self.router.ingest_events(websocket, message)
                else:
                    if not await self.router.authenticate_client(websocket, message):
                        # If this is created by a browser, then 1) server php portal misconfiguration or 2) exploit attempt. Kill connection without response. Log event in Rabbit Log.
                        # If this is created by a node, check to see if the IP address is white-listed. If not, kill connection without response. Log event with IP address.
                        # ---> If IP is white-listed, send response requesting handshake access code (Created by the web portal)
                        if await self.connectionManager.is_ip_whitelisted(websocket.remote_address[0]):
                            if not await self.router.create_chain_of_trust(websocket):
                                print("\tBad trust-chain handshake. Disconnecting.")
                                raise BadCredentials(websocket.remote_address[0])
                            else:
                                print("Chain established")
                        else:
                            raise BadCredentials(websocket.remote_address[0])
        except (websockets.ConnectionClosed):
            # Exception raised when websockets.open() == False
            # Connection is closed. Exit iterator.
            pass
        except BadCredentials as e:
            print(f"\tBad Credentials. Adding attempt from {e.ip_address} to log.")
        finally:
            if self.connectionManager.is_authorized_user(websocket):
                agent = self.connectionManager.get_client(websocket).get_agent()
                await self.connectionManager.detach_client(websocket)
                await self.router.adjust_connected_users_list(agent)
            else:
                await websocket.close()
            print("Client Disconnected")

if __name__ == "__main__":
    ClaverDispatch("192.168.1.25", 6789)




"""
Overview: https://www.aeracode.org/2018/02/19/python-async-simplified/

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

https://websockets.readthedocs.io/en/stable/intro.html
https://websockets.readthedocs.io/en/stable/cheatsheet.html?highlight=handler#passing-additional-arguments-to-the-connection-handler
https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers
https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent#Status_codes
https://stackoverflow.com/questions/45675148/why-are-websockets-connections-constantly-closed-upon-browser-reload


Resources: Sockets
https://realpython.com/python-sockets/


Resources: RabbitMQ
https://www.youtube.com/watch?v=XjuiZM7JzPw

Resources: Kafka
https://switchcaseblog.wordpress.com/2017/01/20/how-to-get-php-and-kafka-to-play-nicely-and-not-do-it-slowly/
https://www.alberton.info/kafka_07_php_client_library.html
https://demyanov.dev/using-php-apache-kafka

Resources: Systemd services
https://unix.stackexchange.com/questions/166473/debian-how-to-run-a-script-on-startup-as-soon-as-there-is-an-internet-connecti/401080#401080
https://stackoverflow.com/questions/13069634/python-daemon-and-systemd-service
https://www.xarg.org/2016/07/how-to-write-a-php-daemon/
"""