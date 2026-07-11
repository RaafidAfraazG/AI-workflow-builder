from typing import AsyncGenerator
from abc import ABC, abstractmethod
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


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


class GeminiLLMProvider(LLMProvider):
    def __init__(self):
        try:
            from google import genai
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model = settings.GEMINI_MODEL
            logger.info(f"GeminiLLMProvider initialized with model: {self.model}")
        except ImportError:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        try:
            from google import genai
            # Use asyncio to run the synchronous streaming in a thread
            loop = asyncio.get_event_loop()
            
            def _generate():
                return list(self.client.models.generate_content_stream(
                    model=self.model,
                    contents=prompt,
                ))
            
            chunks = await loop.run_in_executor(None, _generate)
            for chunk in chunks:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {str(e)}"


class MockLLMProvider(LLMProvider):
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        response = (
            f"This is a mock response to your query: '{prompt[:50]}...'. "
            "The workflow is working correctly with mock LLM provider."
        )
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)


class LLMService:
    def __init__(self):
        provider = settings.LLM_PROVIDER.lower()

        if provider == "gemini" and settings.GEMINI_API_KEY:
            self.provider = GeminiLLMProvider()
        elif provider == "openai" and settings.OPENAI_API_KEY:
            self.provider = OpenAILLMProvider()
        else:
            self.provider = MockLLMProvider()

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        async for token in self.provider.stream(prompt):
            yield token