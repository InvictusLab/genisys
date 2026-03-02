class AgentLoop:

    def __init__(self, query: str):
        self._running = False
        self.query = query

    async def run(self) -> None:
        while self._running:
            pass

    def stop(self) -> None:
        self._running = False



