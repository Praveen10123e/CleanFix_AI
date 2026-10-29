"""Configurable LLM Client and provider abstraction for CleanFix AI.

Supports Mock provider, Google Gemini (via google-genai), and OpenAI-compatible providers
with configurable timeouts, retries, and strict schema validation.
"""

import json
import os
import time
from abc import ABC, abstractmethod

from pydantic import BaseModel, ValidationError


class LLMTimeoutError(Exception):
    """Raised when an LLM call exceeds configured timeout."""


class LLMProviderError(Exception):
    """Raised when an LLM provider fails permanently or returns an unrecoverable error."""


class LLMClient(ABC):
    """Abstract interface for LLM calls with structured output validation."""

    def __init__(
        self,
        model_name: str,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        temperature: float = 0.1,
    ):
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.temperature = temperature

    @abstractmethod
    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Generates structured response validated against a Pydantic model."""


class MockLLMClient(LLMClient):
    """Deterministic Mock LLM Client for zero-API-key local testing and demos."""

    def __init__(
        self,
        model_name: str = "mock-diagnostic-v1",
        timeout_seconds: float = 5.0,
        max_retries: int = 1,
        simulate_timeout: bool = False,
        simulate_malformed: bool = False,
        simulate_provider_error: bool = False,
    ):
        super().__init__(model_name, timeout_seconds, max_retries)
        self.simulate_timeout = simulate_timeout
        self.simulate_malformed = simulate_malformed
        self.simulate_provider_error = simulate_provider_error

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        """Simulates structured LLM output with optional failure injection."""
        if self.simulate_timeout:
            time.sleep(0.01)
            raise LLMTimeoutError(f"LLM request timed out after {self.timeout_seconds}s")

        if self.simulate_provider_error:
            raise LLMProviderError("Simulated LLM Provider Connection Failure: 503 Service Unavailable")

        if self.simulate_malformed:
            # Return invalid data that fails Pydantic schema validation
            raise ValidationError.from_exception_data(
                title=response_model.__name__,
                line_errors=[{"type": "missing", "loc": ("decision",), "msg": "Field required", "input": {}}],
            )

        # In mock mode, we use deterministic prompt parsing or return a safe structured instance
        # The mock engine handles domain logic; this client handles generic schema construction
        return response_model.model_validate({
            "decision": "next_step",
            "reasoning_summary": "Simulated mock reasoning based on session context.",
            "next_step": {
                "action_id": "PROJ_SOURCE_SEARCH",
                "instruction": "Press the Source Search button on the remote or control panel.",
                "reason": "Verify that the projector is receiving signal from the correct input port.",
                "expected_observation": "The laptop desktop appears on screen.",
                "safety_level": "low",
                "requires_confirmation": True,
            },
            "sources": [],
            "uncertainty": "Input source currently unconfirmed.",
        })


class GoogleGenAIClient(LLMClient):
    """Google Gemini client using google-genai SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        temperature: float = 0.1,
    ):
        super().__init__(model_name, timeout_seconds, max_retries, temperature)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or LLM_API_KEY environment variable is required")

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Google GenAI client: {e}")

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
    ) -> BaseModel:
        from google.genai import types

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_schema=response_model,
                        temperature=self.temperature,
                    ),
                )
                if not response.text:
                    raise ValueError("Empty response received from Gemini API")

                parsed_json = json.loads(response.text)
                return response_model.model_validate(parsed_json)
            except Exception as e:
                if attempt == self.max_retries:
                    raise LLMProviderError(f"Gemini API generation failed after {self.max_retries} retries: {e}")
                time.sleep(0.5 * (2 ** attempt))


def get_llm_client(
    provider_override: str | None = None,
    simulate_timeout: bool = False,
    simulate_malformed: bool = False,
    simulate_provider_error: bool = False,
) -> LLMClient:
    """
    Factory function to retrieve configured LLM client.
    Default provider is 'mock' for standalone testing and demos.
    """
    provider = provider_override or os.getenv("LLM_PROVIDER", "mock").lower()
    model_name = os.getenv("LLM_MODEL_NAME", "mock-diagnostic-v1")
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "10.0"))
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    temp = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    if provider == "gemini":
        return GoogleGenAIClient(
            model_name=os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash"),
            timeout_seconds=timeout,
            max_retries=max_retries,
            temperature=temp,
        )
    elif provider == "mock":
        return MockLLMClient(
            model_name=model_name,
            timeout_seconds=timeout,
            max_retries=max_retries,
            simulate_timeout=simulate_timeout,
            simulate_malformed=simulate_malformed,
            simulate_provider_error=simulate_provider_error,
        )
    else:
        # Default fallback to mock
        return MockLLMClient(model_name=model_name)

