from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import certifi
import ssl
import yaml

from src.env_loader import load_env


@dataclass
class LLMResponse:
    content: str
    model: str


class OpenAICompatibleProvider:
    def __init__(
        self,
        config_path: Path = Path("configs/triage_model.yaml"),
        allow_fallback: bool | None = None,
        max_retry_attempts: int | None = None,
        retry_sleep_seconds: float | None = None,
    ) -> None:
        load_env()
        config = load_yaml(config_path)
        provider_name = config.get("provider", "openrouter")
        provider_config = config.get("providers", {}).get(provider_name, {})
        retry_config = config.get("retry", {})
        fallback_config = config.get("fallback", {})
        self.provider_name = provider_name
        self.base_url = provider_config.get("base_url", "").rstrip("/")
        self.api_key = os.environ.get(provider_config.get("api_key_env", ""))
        self.default_model = provider_config.get("default_model")
        self.fallback_models = provider_config.get("fallback_models", [])
        self.site_url = os.environ.get(provider_config.get("site_url_env", ""), "")
        self.app_name = os.environ.get(provider_config.get("app_name_env", ""), "")
        self.allow_fallback = (
            bool(fallback_config.get("enabled", False))
            if allow_fallback is None
            else allow_fallback
        )
        self.max_retry_attempts = max_retry_attempts or int(
            retry_config.get("max_attempts", 3)
        )
        self.retry_sleep_seconds = retry_sleep_seconds or float(
            retry_config.get("sleep_seconds", 10)
        )

    @property
    def models(self) -> list[str]:
        models = [self.default_model]
        if self.allow_fallback:
            models.extend(self.fallback_models)
        return [model for model in models if model]

    def chat(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError(f"Missing API key for provider: {self.provider_name}")

        last_error: Exception | None = None
        for model in self.models:
            for attempt in range(1, self.max_retry_attempts + 1):
                try:
                    return LLMResponse(
                        content=self._chat_with_model(model, system_prompt, user_prompt),
                        model=model,
                    )
                except Exception as error:
                    last_error = error
                    if attempt < self.max_retry_attempts:
                        print(
                            "WARNING: Triage model failed; retrying. "
                            f"Model: {model}. Attempt: {attempt}/{self.max_retry_attempts}. "
                            f"Error: {error}"
                        )
                        time.sleep(self.retry_sleep_seconds)
                    else:
                        print(
                            "WARNING: Triage model failed. "
                            f"Model: {model}. Attempts: {self.max_retry_attempts}. "
                            f"Error: {error}"
                        )
            if not self.allow_fallback:
                break
        raise RuntimeError(f"All triage models failed: {last_error}")

    def _chat_with_model(self, model: str, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        context = ssl.create_default_context(cafile=certifi.where())
        try:
            with urlopen(request, timeout=60, context=context) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"HTTP {error.code} from {self.provider_name} for model {model}: {body}"
            ) from error
        return data["choices"][0]["message"]["content"]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
