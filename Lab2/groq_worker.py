from __future__ import annotations

import os
import json
from typing import List, Dict

from PySide6.QtCore import QThread, Signal
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL_ID, TEMPERATURE, MAX_TOKENS


def _leer_archivo(path: str, fallback: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return fallback.strip()


class GroqWorker(QThread):
    finished = Signal(str)  # contenido JSON puro (str)
    failed = Signal(str)

    def __init__(self, problem_text: str) -> None:
        super().__init__()
        self.problem_text = (problem_text or "").strip()
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS

    def _mensajes_chat(self, prompt_usuario_base: str, prompt_sistema: str) -> List[Dict[str, str]]:
        # El prompt de usuario debe exigir JSON puro
        return [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario_base + ("\n\n" + self.problem_text if self.problem_text else "")},
        ]

    def run(self) -> None:
        try:
            api_key = (GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")).strip()
            if not api_key:
                raise RuntimeError("No se encontró GROQ_API_KEY (.env o variable de entorno).")

            cliente = Groq(api_key=api_key)

            prompt_sistema = _leer_archivo(
                "system_prompt.txt",
                fallback="Eres un analista de PL. Devuelve SOLO JSON válido, sin texto extra.",
            )
            prompt_usuario_base = _leer_archivo(
                "user_prompt.txt",
                fallback=(
                    "Responde SOLO JSON válido con el esquema solicitado. "
                    "No incluyas comentarios, disculpas ni texto fuera del JSON."
                ),
            )

            mensajes = self._mensajes_chat(prompt_usuario_base, prompt_sistema)
            respuesta = cliente.chat.completions.create(
                model=GROQ_MODEL_ID,
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
                messages=mensajes,
            )

            contenido = respuesta.choices[0].message.content if respuesta.choices else ""

            # Validar que sea JSON puro
            try:
                _ = json.loads(contenido)
            except Exception as exc:
                raise RuntimeError(f"La respuesta de la IA no es JSON válido: {exc}")

            self.finished.emit(contenido)

        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
