import json
import logging
from typing import Tuple
logging.basicConfig()
from server.connections.ConnectionManager import ConnectionManager

class EventManager:
    STATE = {"value": 0}

    def __init__(self, connectionManager: ConnectionManager):
        self.connectionManager = connectionManager

    def state_event(self) -> str:
        return json.dumps({"type": "state", **self.STATE})

    def users_event(self) -> str:
        return json.dumps({"type": "users", "count": self.connectionManager.get_client_count()})

    def decode_event(self, data: str) -> dict:
        response = {}
        response["error"] = False
        response["target"] = "all"
        if "action" in data:
            if data["action"] == "minus":
                self.STATE["value"] -= 1
                response["event"] = self.state_event()
                return response
            elif data["action"] == "plus":
                self.STATE["value"] += 1
                response["event"] = self.state_event()
                return response
            else:
                logging.error("Unsupported event: {}", data)
        else:
            response["error"] = True
            return response

    def get_state(self):
        return self.state_event()