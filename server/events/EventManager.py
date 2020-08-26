import json
import logging
from typing import Tuple
logging.basicConfig()
from server.users.UserManager import UserManager

class EventManager:
    STATE = {"value": 0}

    def __init__(self, clientManager: UserManager):
        self.clientManager = clientManager

    def state_event(self) -> str:
        return json.dumps({"type": "state", **self.STATE})

    def users_event(self) -> str:
        return json.dumps({"type": "users", "count": self.clientManager.get_client_count()})

    def decode_event(self, data: str) -> Tuple[str, int]:
        if data["action"] == "minus":
            self.STATE["value"] -= 1
            return self.state_event(), -1
        elif data["action"] == "plus":
            self.STATE["value"] += 1
            return self.state_event(), -1
        else:
            logging.error("Unsupported event: {}", data)

    def get_state(self):
        return self.state_event()