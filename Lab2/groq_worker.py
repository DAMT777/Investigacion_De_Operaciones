from __future__ import annotations
import os
from PySide6.QtCore import QThread, Signal
from groq import Groq
from config import (
    GROQ_API_KEY, GROQ_MODEL_ID,
    TEMPERATURE, MAX_TOKENS
)

def _load_prompt(path: str, fallback: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return fallback.strip()


class GroqWorker(QThread):
    finished = Signal(str)   
    failed   = Signal(str)   

    def __init__(self, problem_text: str):
        super().__init__()
        self.problem_text = (problem_text or "").strip()
        self.temperature  = TEMPERATURE
        self.max_tokens   = MAX_TOKENS

    def _build_text_messages(self, base_user: str, system_prompt: str, body_text: str):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": base_user + ("\n\n" + body_text if body_text else "")},
        ]

    def run(self):
        try:
            api_key = (GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")).strip()
            if not api_key:
                raise RuntimeError("No se encontró GROQ_API_KEY (.env o variable de entorno).")

            client = Groq(api_key=api_key)
            
            system_prompt = _load_prompt(
                "system_prompt.txt",
                fallback="Eres un analista de PL. Devuelve solo texto plano con variables, FO, restricciones y no negatividad."
            )
            base_user = _load_prompt(
                "user_prompt.txt",
                fallback="Interpreta el enunciado (método gráfico) y devuelve las secciones solicitadas."
            )

            messages_text = self._build_text_messages(base_user, system_prompt, self.problem_text)
            res = client.chat.completions.create(
                model=GROQ_MODEL_ID,
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
                messages=messages_text,
            )
            text = res.choices[0].message.content if res.choices else "(Sin contenido)"
            self.finished.emit(text)
            return

        except Exception as e:
            self.failed.emit(str(e))
