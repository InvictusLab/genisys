from abc import abstractmethod, ABC


class LLMProvider(ABC):

    def __init__(self, api_base_url: str | None = None, api_key: str | None = None) -> None:
        self.api_base_url = api_base_url
        self.api_key = api_key

    @abstractmethod
    def get_default_model(self) -> str:
        pass

    @abstractmethod
    async def chat(self):
        pass

    @abstractmethod
    def _clear_empty_content(self):
        pass


