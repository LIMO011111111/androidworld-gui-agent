"""The model clients, against a local stand-in HTTP server."""

import http.server
import json
import threading

import pytest

from gui_agent import actions
from gui_agent import config as config_lib
from gui_agent import model as model_lib


class _Server:
  """Answers like Ollama / an OpenAI-compatible server and records requests."""

  def __init__(self):
    self.requests = []
    self.fail_next = 0
    self.reject_schema = False
    outer = self

    class Handler(http.server.BaseHTTPRequestHandler):
      def log_message(self, *args):  # silence
        pass

      def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

      def do_GET(self):
        if self.path == "/api/version":
          self._send(200, {"version": "0.12.7"})
        elif self.path == "/api/tags":
          self._send(200, {"models": [{"name": "qwen3-vl:4b-instruct", "digest": "ee4b975b58c1ffff"}]})
        else:
          self._send(404, {})

      def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        outer.requests.append({"path": self.path, "body": body,
                               "auth": self.headers.get("Authorization")})
        if outer.fail_next > 0:
          outer.fail_next -= 1
          self._send(503, {"error": "loading model"})
        elif outer.reject_schema and isinstance(body.get("format"), dict):
          self._send(400, {"error": "invalid JSON schema in format"})
        elif self.path == "/api/chat":
          self._send(200, {
              "message": {"role": "assistant", "content": '{"thought": "t", "action_type": "wait"}'},
              "prompt_eval_count": 812, "eval_count": 17,
          })
        elif self.path == "/api/show":
          self._send(200, {"details": {"parameter_size": "4.4B", "quantization_level": "Q4_K_M", "family": "qwen3vl"}})
        elif self.path == "/v1/chat/completions":
          self._send(200, {
              "choices": [{"message": {"content": '{"action_type": "wait"}'}}],
              "usage": {"prompt_tokens": 900, "completion_tokens": 9},
          })
        else:
          self._send(404, {"error": "not found"})

    self._httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    self.url = f"http://127.0.0.1:{self._httpd.server_address[1]}"
    threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

  def close(self):
    self._httpd.shutdown()


@pytest.fixture()
def server():
  srv = _Server()
  yield srv
  srv.close()


MESSAGES = [
    {"role": "system", "content": "rules"},
    {"role": "user", "content": "screen", "images": ["QUJD"]},
]


def test_ollama_request_carries_schema_options_and_image(server):
  cfg = config_lib.AgentConfig(base_url=server.url)
  client = model_lib.OllamaClient(cfg)
  schema = actions.action_schema("index", cfg.allowed_apps, True)
  reply = client.chat(MESSAGES, schema)
  assert reply.text == '{"thought": "t", "action_type": "wait"}'
  assert (reply.prompt_tokens, reply.completion_tokens) == (812, 17)
  body = server.requests[0]["body"]
  assert body["model"] == "qwen3-vl:4b-instruct" and body["stream"] is False
  assert body["format"] == schema  # constrained decoding
  assert body["options"] == {"temperature": 0.0, "seed": 42, "num_ctx": 8192, "num_predict": 400}
  assert body["messages"][1]["images"] == ["QUJD"]
  assert "think" not in body  # only sent when configured


def test_ollama_identity_records_quantisation_and_digest(server):
  info = model_lib.OllamaClient(config_lib.AgentConfig(base_url=server.url)).describe()
  assert info["quantization"] == "Q4_K_M" and info["digest"] == "ee4b975b58c1"
  assert info["ollama_version"] == "0.12.7"


def test_transient_server_errors_are_retried(server, monkeypatch):
  monkeypatch.setattr(model_lib.time, "sleep", lambda _: None)
  server.fail_next = 2
  client = model_lib.OllamaClient(config_lib.AgentConfig(base_url=server.url))
  assert client.chat(MESSAGES).text
  assert len(server.requests) == 3


def test_persistent_failure_raises_a_model_error(server, monkeypatch):
  monkeypatch.setattr(model_lib.time, "sleep", lambda _: None)
  server.fail_next = 99
  client = model_lib.OllamaClient(config_lib.AgentConfig(base_url=server.url))
  with pytest.raises(model_lib.ModelError, match="503"):
    client.chat(MESSAGES)


def test_openai_compatible_client_converts_images_and_sends_the_key(server, monkeypatch):
  monkeypatch.setenv("MY_TEST_KEY", "secret")
  cfg = config_lib.AgentConfig(
      backend="openai", base_url=server.url + "/v1", model="some-model",
      api_key_env="MY_TEST_KEY",
  )
  reply = model_lib.make_client(cfg).chat(MESSAGES)
  assert reply.text == '{"action_type": "wait"}' and reply.prompt_tokens == 900
  request = server.requests[0]
  assert request["auth"] == "Bearer secret"
  parts = request["body"]["messages"][1]["content"]
  assert parts[0] == {"type": "text", "text": "screen"}
  assert parts[1]["image_url"]["url"] == "data:image/jpeg;base64,QUJD"
  assert request["body"]["response_format"] == {"type": "json_object"}


def test_missing_api_key_is_reported_clearly(monkeypatch):
  monkeypatch.delenv("NO_SUCH_KEY", raising=False)
  cfg = config_lib.AgentConfig(backend="openai", api_key_env="NO_SUCH_KEY")
  with pytest.raises(model_lib.ModelError, match="NO_SUCH_KEY"):
    model_lib.make_client(cfg)


def test_log_copy_of_messages_has_no_image_bytes():
  redacted = model_lib.redact_messages(MESSAGES)
  assert redacted[1]["images"] == "<1 image(s) omitted>"
  assert MESSAGES[1]["images"] == ["QUJD"]  # the original is untouched


def test_falls_back_to_json_mode_when_the_server_rejects_the_schema(server):
  server.reject_schema = True
  client = model_lib.OllamaClient(config_lib.AgentConfig(base_url=server.url))
  schema = actions.action_schema("index", ("markor",), False)
  assert client.chat(MESSAGES, schema).text
  assert client.chat(MESSAGES, schema).text
  formats = [r["body"]["format"] for r in server.requests]
  # One rejected attempt, then plain JSON mode for this and every later call.
  assert formats == [schema, "json", "json"]
