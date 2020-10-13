import asyncio


class StateSentinel:
    def __init__(self):
        self.task_push_request = None
        self.refresh_interval = None
        self.active = True
        self.static_state_func = None

    @classmethod
    async def initialize(cls, event_loop, connectionManager, construct_state_func, refresh_interval):
        self = StateSentinel()
        self.static_state_func = construct_state_func
        self.connectionManager = connectionManager
        self.refresh_interval = refresh_interval
        self.task_push_request = event_loop.create_task(self.refresh_state())
        return self

    async def refresh_state(self):
        while self.active:
            state_values = self.static_state_func()
            print(f"State vals: {state_values}")
            # await self.messageBus.broadcast_event_update_by_key(json.dumps(state_values["state_values"]), dashboard_type)
            await asyncio.sleep(self.refresh_interval)

    def cleanup(self):
        self.active = False
        self.task_push_request.cancel()
