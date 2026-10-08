"""Model access.

One small interface (`chat`) with two transports, so the model is a config
value and not a code change ("any model you like - record its name"):

* `OllamaClient`  - native Ollama API, used for local models. Supports
  JSON-schema constrained decoding through the `format` field.
* `OpenAICompatClient` - any OpenAI-compatible `/chat/completions` endpoint
  (OpenAI, Gemini, OpenRouter, vLLM, or Ollama's own /v1).

Messages use one neutral shape everywhere in the agent:
    {"role": "system" | "user" | "assistant", "content": str, "images": [b64]}
The role structure is kept standard on purpose (Day 2: let the chat template
render roles; do not hand-format the conversation into one string).
"""

from __future__ import annotations

import dataclasses
import json
import os
import time
from typing import Any, Optional, Protocol

import requests

from gui_agent import config as config_lib


@dataclasses.dataclass
class ModelReply:
  text: str
  latency_s: float = 0.0
  prompt_tokens: Optional[int] = None
  completion_tokens: Optional[int] = None
  thinking: str = ""


class ModelError(RuntimeError):
  """The model server could not be reached or returned an error."""


class ModelClient(Protocol):
  """What the agent needs from a model."""

  name: str

  def chat(
      self, messages: list[dict[str, Any]], schema: Optional[dict[str, Any]] = None
  ) -> ModelReply:
    ...

  def describe(self) -> dict[str, Any]:
    ...


class OllamaClient:
  """Native Ollama `/api/chat` client."""

  def __init__(self, cfg: config_lib.AgentConfig):
    self.name = cfg.model
    self._cfg = cfg
    self._url = cfg.base_url.rstrip("/")
    self._schema_ok = True  # until the server rejects a schema once

  def chat(self, messages, schema=None) -> ModelReply:
    payload: dict[str, Any] = {
        "model": self._cfg.model,
        "messages": [_ollama_message(m) for m in messages],
        "stream": False,
        "keep_alive": "30m",
        "options": {
            "temperature": self._cfg.temperature,
            "seed": self._cfg.seed,
            "num_ctx": self._cfg.num_ctx,
            "num_predict": self._cfg.max_output_tokens,
        },
    }
    if self._cfg.think is not None:
      payload["think"] = self._cfg.think
    use_schema = schema is not None and self._schema_ok
    if self._cfg.constrain_output:
      payload["format"] = schema if use_schema else "json"
    start = time.perf_counter()
    url = f"{self._url}/api/chat"
    try:
      data = _post_json(url, payload, {}, self._cfg.request_timeout_s)
    except ModelError as error:
      if not (use_schema and self._cfg.constrain_output and "HTTP 400" in str(error)):
        raise
      # This server or model build does not accept a JSON schema. Fall back
      # to plain JSON mode for the rest of the run; validation and retry in
      # actions.parse_action still apply.
      print(f"[model] schema-constrained output rejected, using JSON mode: {error}")
      self._schema_ok = False
      payload["format"] = "json"
      data = _post_json(url, payload, {}, self._cfg.request_timeout_s)
    latency = time.perf_counter() - start
    message = data.get("message") or {}
    return ModelReply(
        text=message.get("content") or "",
        thinking=message.get("thinking") or "",
        latency_s=latency,
        prompt_tokens=data.get("prompt_eval_count"),
        completion_tokens=data.get("eval_count"),
    )

  def describe(self) -> dict[str, Any]:
    """Model identity for the run metadata.

    Quantisation and digest are recorded because "if you change quantisation,
    or switch model, re-run your evaluation - it is a different model".
    """
    info: dict[str, Any] = {
        "backend": "ollama",
        "model": self._cfg.model,
        "base_url": self._url,
        "temperature": self._cfg.temperature,
        "seed": self._cfg.seed,
        "num_ctx": self._cfg.num_ctx,
    }
    try:
      shown = _post_json(f"{self._url}/api/show", {"model": self._cfg.model}, {}, 15)
      details = shown.get("details") or {}
      info["parameter_size"] = details.get("parameter_size")
      info["quantization"] = details.get("quantization_level")
      info["family"] = details.get("family")
      tags = requests.get(f"{self._url}/api/tags", timeout=15).json()
      for entry in tags.get("models", []):
        if entry.get("name") == self._cfg.model or entry.get("model") == self._cfg.model:
          info["digest"] = (entry.get("digest") or "")[:12]
      info["ollama_version"] = requests.get(
          f"{self._url}/api/version", timeout=15
      ).json().get("version")
      info["output_format"] = (
          "json schema" if self._cfg.constrain_output and self._schema_ok
          else "json" if self._cfg.constrain_output else "free text"
      )
    except Exception as error:  # metadata only, never fail a run for it
      info["describe_error"] = str(error)
    return info


class OpenAICompatClient:
  """Client for any OpenAI-compatible chat completions endpoint."""

  def __init__(self, cfg: config_lib.AgentConfig):
    self.name = cfg.model
    self._cfg = cfg
    self._url = cfg.base_url.rstrip("/")
    self._key = os.environ.get(cfg.api_key_env, "") if cfg.api_key_env else ""
    if cfg.api_key_env and not self._key:
      raise ModelError(
          f"Environment variable {cfg.api_key_env} is not set (API key)."
      )

  def chat(self, messages, schema=None) -> ModelReply:
    payload: dict[str, Any] = {
        "model": self._cfg.model,
        "messages": [_openai_message(m) for m in messages],
        "temperature": self._cfg.temperature,
        "max_tokens": self._cfg.max_output_tokens,
    }
    if self._cfg.constrain_output:
      payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {self._key}"} if self._key else {}
    start = time.perf_counter()
    url = f"{self._url}/chat/completions"
    try:
      data = _post_json(url, payload, headers, self._cfg.request_timeout_s)
    except ModelError as error:
      if "max_tokens" not in str(error):
        raise
      # Newer OpenAI models renamed the parameter.
      payload["max_completion_tokens"] = payload.pop("max_tokens")
      data = _post_json(url, payload, headers, self._cfg.request_timeout_s)
    latency = time.perf_counter() - start
    try:
      message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
      raise ModelError(f"Unexpected response: {json.dumps(data)[:300]}") from None
    usage = data.get("usage") or {}
    content = message.get("content") or ""
    if isinstance(content, list):  # some servers return content parts
      content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return ModelReply(
        text=content,
        thinking=message.get("reasoning_content") or message.get("reasoning") or "",
        latency_s=latency,
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
    )

  def describe(self) -> dict[str, Any]:
    return {
        "backend": "openai-compatible",
        "model": self._cfg.model,
        "base_url": self._url,
        "temperature": self._cfg.temperature,
    }


def make_client(cfg: config_lib.AgentConfig) -> ModelClient:
  if cfg.backend == "ollama":
    return OllamaClient(cfg)
  return OpenAICompatClient(cfg)


# --- helpers -----------------------------------------------------------------


def _ollama_message(message: dict[str, Any]) -> dict[str, Any]:
  out = {"role": message["role"], "content": message["content"]}
  if message.get("images"):
    out["images"] = list(message["images"])
  return out


def _openai_message(message: dict[str, Any]) -> dict[str, Any]:
  images = message.get("images") or []
  if not images:
    return {"role": message["role"], "content": message["content"]}
  parts: list[dict[str, Any]] = [{"type": "text", "text": message["content"]}]
  for b64 in images:
    parts.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
    })
  return {"role": message["role"], "content": parts}


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
    attempts: int = 3,
) -> dict[str, Any]:
  """POST with a small retry for transient failures (API layer, Day 4)."""
  last_error = ""
  for attempt in range(1, attempts + 1):
    try:
      response = requests.post(url, json=payload, headers=headers, timeout=timeout)
      if response.status_code == 200:
        return response.json()
      last_error = f"HTTP {response.status_code}: {response.text[:300]}"
      if response.status_code not in (408, 429, 500, 502, 503, 504):
        break  # a client error will not get better by retrying
    except requests.RequestException as error:
      last_error = f"{type(error).__name__}: {error}"
    except ValueError as error:  # body was not JSON
      last_error = f"Invalid JSON from server: {error}"
    if attempt < attempts:
      time.sleep(2.0 * attempt)
  raise ModelError(f"Model request to {url} failed. {last_error}")


def redact_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
  """Copy of the messages without image bytes, for the trajectory log."""
  out = []
  for m in messages:
    entry = {"role": m["role"], "content": m["content"]}
    if m.get("images"):
      entry["images"] = f"<{len(m['images'])} image(s) omitted>"
    out.append(entry)
  return out
