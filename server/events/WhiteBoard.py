from server.connections.ConnectionManager import ConnectionManager


class WhiteBoard:
    STATE = {"value": 0}

    def __init__(self, connectionManager: ConnectionManager):
        self.connectionManager = connectionManager

    def state_event(self) -> dict:
        return {"type": "state", **self.STATE}

    def users_event(self) -> dict:
        return {"type": "users", "count": self.connectionManager.get_client_count()}

    def process_event(self, data: dict, response: dict) -> None:
        if "action" in data:
            if data["action"] == "minus":
                self.STATE["value"] -= 1
                response["event"] = self.state_event()
            elif data["action"] == "plus":
                self.STATE["value"] += 1
                response["event"] = self.state_event()
            else:
               response["error"] = "Unsupported event: {}".format(data["action"])
        else:
            response["error"] = True

    def get_state(self) -> dict:
        return self.state_event()

    def get_users(self) -> dict:
        return self.users_event()