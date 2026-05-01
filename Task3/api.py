"""
Gemini API wrapper (streaming + JSON parsing).
"""

from __future__ import annotations

import os
from typing import Type

from google import genai
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .trace_utils import traceable


def _get_client() -> genai.Client:
    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # If API key exists, create client using it
    if api_key:
        return genai.Client(api_key=api_key)
    
    # Otherwise create client without API key (default setup)
    return genai.Client()


@traceable(name="render_messages")
def _render_messages(messages: list[BaseMessage]) -> str:
    # Convert list of messages into a single formatted string
    parts: list[str] = []

    for msg in messages:
        # Get role (user, assistant, etc.), default = user
        role = getattr(msg, "type", "user")

        # Get message content
        content = msg.content

        # If content is list, join only string parts
        if isinstance(content, list):
            content_text = "".join(
                item for item in content if isinstance(item, str)
            )
        else:
            # Convert content to string
            content_text = str(content)

        # Add formatted message to parts
        parts.append(f"{role.upper()}:\n{content_text}")

    # Join all messages with spacing
    return "\n\n".join(parts)


@traceable(name="parse_model_json")
def _parse_model_json(raw_text: str, schema_model: Type[BaseModel]) -> BaseModel:
    return schema_model.model_validate_json(raw_text)


@retry(
    # Retry only if ValueError or ValidationError occurs
    retry=retry_if_exception_type((ValueError, ValidationError)),

    # Maximum 3 retry attempts
    stop=stop_after_attempt(3),

    # Wait time increases exponentially between retries
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),

    # Raise final error if all retries fail
    reraise=True,
)
@traceable(name="generate_and_parse")
def _generate_and_parse(
    client: genai.Client,
    prompt: str,
    schema_model: Type[BaseModel],
) -> tuple[str, BaseModel]:
    
    # Call Gemini model to generate response
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )

    # Get text output from response
    raw_text = response.text or ""

    # If response is empty, raise error to trigger retry
    if not raw_text.strip():
        raise ValueError("LLM returned empty response")

    # Parse JSON output into Pydantic model
    parsed = _parse_model_json(raw_text, schema_model)

    # Return both raw text and parsed object
    return raw_text, parsed


@traceable(name="stream_json")
def stream_json(
    messages: list[BaseMessage],
    schema_model: Type[BaseModel],
    temperature: float,
) -> tuple[str, BaseModel]:
    """Call Gemini output and parse JSON into Pydantic model."""

    # Create Gemini client
    client = _get_client()

    # Convert messages into prompt string
    prompt = _render_messages(messages)

    # Generate response and parse it
    return _generate_and_parse(client=client, prompt=prompt, schema_model=schema_model)