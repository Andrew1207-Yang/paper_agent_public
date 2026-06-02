from __future__ import annotations

import json
import os
import ssl
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import certifi
import yaml

from src.env_loader import load_env


class EmbeddingProvider:
    def __init__(self, config_path: Path = Path("configs/retrieval_settings.yaml")) -> None:
        load_env()
        config = load_yaml(config_path).get("embedding_model", {})
        self.base_url = str(config.get("base_url", "")).rstrip("/")
        self.api_key = os.environ.get(str(config.get("api_key_env", "")))
        self.model = str(config.get("model", "nvidia/nv-embed-v1"))
        self.batch_size = int(config.get("batch_size", 32))

    def embed(
        self, texts: list[str], input_type: str, debug: bool = False
    ) -> list[list[float]]:
        if not texts:
            return []
        if not self.api_key:
            raise RuntimeError("Missing NVIDIA_API_KEY for embedding provider")

        embeddings: list[list[float]] = []
        batches = chunked(texts, self.batch_size)
        if debug:
            print(
                f"Embedding request plan: texts={len(texts)}, "
                f"batches={len(batches)}, model={self.model}, input_type={input_type}"
            )
        for index, batch in enumerate(batches, start=1):
            if debug:
                print(f"Sending embedding batch {index}/{len(batches)}: size={len(batch)}")
            batch_embeddings = self._embed_batch(batch, input_type=input_type, debug=debug)
            embeddings.extend(batch_embeddings)
            if debug:
                print(
                    f"Parsed embedding batch {index}/{len(batches)}: "
                    f"received={len(batch_embeddings)}"
                )
        return embeddings

    def _embed_batch(
        self, texts: list[str], input_type: str, debug: bool = False
    ) -> list[list[float]]:
        payload = {
            "model": self.model,
            "input": texts,
            "input_type": input_type,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        request = Request(
            f"{self.base_url}/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        context = ssl.create_default_context(cafile=certifi.where())
        try:
            if debug:
                print(
                    "Embedding payload: "
                    f"input_format=list[str], input_count={len(texts)}, "
                    f"single_api_call=true"
                )
            with urlopen(request, timeout=90, context=context) as response:
                raw_body = response.read().decode("utf-8")
                if debug:
                    print(
                        f"Received embedding response: status={response.status}, "
                        f"bytes={len(raw_body)}"
                    )
                data = json.loads(raw_body)
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Embedding request failed: HTTP {error.code}: {body}") from error
        embeddings = [item["embedding"] for item in data.get("data", [])]
        if debug and embeddings:
            print(f"First embedding dimension: {len(embeddings[0])}")
        return embeddings


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}
