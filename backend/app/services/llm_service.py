from typing import AsyncGenerator
from abc import ABC, abstractmethod
import asyncio
from app.core.config import settings

class LLMProvider(ABC):
    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        pass

class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        try:
            import openai
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            raise ImportError("openai package not installed")

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                temperature=0.7
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"

class MockLLMProvider(LLMProvider):
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        response = f"This is a mock response to your query: '{prompt[:50]}...'. " \
                  "The workflow is working correctly with mock LLM provider."
        
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)  # Simulate streaming delay

class LLMService:
    def __init__(self):
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            self.provider = OpenAILLMProvider()
        else:
            self.provider = MockLLMProvider()

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        async for token in self.provider.stream(prompt):
            yield token