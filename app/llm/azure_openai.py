"""Azure OpenAI LLM Integration"""


class AzureOpenAIClient:
    """Azure OpenAI Client for LLM interactions"""

    def __init__(self, api_key: str, api_version: str, endpoint: str):
        """
        Initialize Azure OpenAI Client

        Args:
            api_key: Azure OpenAI API key
            api_version: API version
            endpoint: Azure OpenAI endpoint
        """
        self.api_key = api_key
        self.api_version = api_version
        self.endpoint = endpoint

    def get_completion(self, prompt: str, **kwargs) -> str:
        """
        Get completion from Azure OpenAI

        Args:
            prompt: Input prompt
            **kwargs: Additional parameters

        Returns:
            Model completion response
        """
        pass

    def get_embedding(self, text: str) -> list:
        """
        Get embedding from Azure OpenAI

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass
