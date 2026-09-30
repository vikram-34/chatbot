"""
LLM Provider Abstraction Layer
-------------------------------
Gemini implementation behind a common LLMProvider interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from app.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        history: List[Dict[str, str]],
        user_message: str
    ) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):

    def __init__(self, api_key: str = None, model_name: str = None):
        api_key = api_key or settings.GEMINI_API_KEY

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name or settings.GEMINI_MODEL

        print(f"Using Gemini model: {self.model_name}")

    @staticmethod
    def _to_gemini_contents(
        history: List[Dict[str, str]],
        user_message: str
    ) -> List[types.Content]:

        contents = []

        for turn in history:
            role = (
                "model"
                if turn["role"] == "assistant"
                else "user"
            )

            contents.append(
                types.Content(
                    role=role,
                    parts=[
                        types.Part(
                            text=turn["content"]
                        )
                    ]
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(text=user_message)
                ]
            )
        )

        return contents

    def generate(
        self,
        history: List[Dict[str, str]],
        user_message: str
    ) -> str:

        contents = self._to_gemini_contents(
            history,
            user_message
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low"
                    )
                ),
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except ClientError as e:

            if e.code == 429:
                raise RuntimeError(
                    "Gemini quota exhausted or rate limit reached. "
                    "Please wait and try again."
                ) from e

            if e.code in (401, 403):
                raise RuntimeError(
                    "Gemini authentication failed. "
                    "Check GEMINI_API_KEY."
                ) from e

            raise RuntimeError(
                f"Gemini request failed: {e.code} - {e.message}"
            ) from e

        except ServerError as e:

            if e.code == 503:
                raise RuntimeError(
                    "Gemini is temporarily overloaded. "
                    "Please try again shortly."
                ) from e

            raise RuntimeError(
                f"Gemini server error: {e.code} - {e.message}"
            ) from e


def get_llm_provider() -> LLMProvider:
    return GeminiProvider()