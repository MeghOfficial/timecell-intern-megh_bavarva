"""
Groq API wrapper (streaming + JSON parsing).
"""

from __future__ import annotations

import os
from typing import Type

from dotenv import load_dotenv
from groq import Groq
from langchain_core.messages import BaseMessage
from pydantic import BaseModel
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .trace_utils import traceable


load_dotenv()


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing")
    return Groq(api_key=api_key)


@traceable(name="render_messages")
def _render_messages(messages: list[BaseMessage]) -> list[dict[str, str]]:
    # Convert LangChain messages into Groq chat-completions payload
    parts: list[dict[str, str]] = []

    for msg in messages:
        role = getattr(msg, "type", "user")
        if role == "human":
            role = "user"
        elif role not in {"system", "user", "assistant"}:
            role = "user"

        content = msg.content

        if isinstance(content, list):
            content_text = "".join(
                item for item in content if isinstance(item, str)
            )
        else:
            content_text = str(content)

        parts.append({"role": role, "content": content_text})

    return parts


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
    client: Groq,
    messages: list[dict[str, str]],
    schema_model: Type[BaseModel],
    temperature: float,
) -> tuple[str, BaseModel]:

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Stream the response from Groq and collect chunks into a single string
    stream = client.chat.completions.create(
        messages=messages,
        model=model_name,
        temperature=temperature,
        max_completion_tokens=2048,
        top_p=1,
        stream=True,
    )

    raw_parts: list[str] = []
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            raw_parts.append(delta)

    raw_text = "".join(raw_parts)

    if not raw_text.strip():
        raise ValueError("LLM returned empty response")

    parsed = _parse_model_json(raw_text, schema_model)

    return raw_text, parsed


@traceable(name="stream_json")
def stream_json(
    messages: list[BaseMessage],
    schema_model: Type[BaseModel],
    temperature: float,
) -> tuple[str, BaseModel]:
    """Call Groq output and parse JSON into Pydantic model."""

    # Create Groq client
    client = _get_client()

    # Convert messages into Groq chat-completions format
    groq_messages = _render_messages(messages)

    # Generate response and parse it
    return _generate_and_parse(
        client=client,
        messages=groq_messages,
        schema_model=schema_model,
        temperature=temperature,
    )