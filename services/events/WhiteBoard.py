from server.connections.ConnectionManager import ConnectionManager


class WhiteBoard:
    STATE = {"value": 0}

    def state_event(self) -> dict:
        return {"type": "whiteboard", **self.STATE}

    def process_event(self, data: dict) -> dict:
        if "action" in data:
            if data["action"] == "minus":
                self.STATE["value"] -= 1
                return self.state_event()
            elif data["action"] == "plus":
                self.STATE["value"] += 1
                return self.state_event()
            else:
                print("Unsupported event: {}".format(data["action"]))

    def get_state(self) -> dict:
        return self.state_event()
