from server.events.WhiteBoard import WhiteBoard
from server.connections.ConnectionManager import ConnectionManager


class EventManager:
    def __init__(self, connectionManager: ConnectionManager):
        self.connectionManager = connectionManager
        self.white_board = WhiteBoard(connectionManager)

    def decode_event(self, data: dict) -> dict:
        response = {}
        response["error"] = ""
        response["target"] = "all"
        response["event"] = ""

        if "mode" in data:
            if data["mode"] == "WhiteBoard":
                self.white_board.process_event(data, response)
        else:
            response["error"] = "EventManager: Bad Event"
        return response

    def get_mode_state(self, mode) -> dict:
        if mode == "WhiteBoard":
            return self.white_board.get_state()
        return {}

    def shim_users(self):
        return self.white_board.get_users()

