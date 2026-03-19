from providers.qwen import QwenProvider


class AgentLoop:
    def __init__(
        self,
        query: str,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        self._running = False
        self.query = query
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def run(self) -> str:
        provider = QwenProvider(api_key=self.api_key, base_url=self.base_url)
        if not provider.api_key:
            raise ValueError("Missing API key. Set QWEN_API_KEY or pass --api-key.")
        response = await provider.chat(
            messages=[{"role": "user", "content": self.query}],
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.content or ""

    def stop(self) -> None:
        self._running = False
