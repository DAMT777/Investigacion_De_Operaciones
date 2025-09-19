import os
from dotenv import load_dotenv

load_dotenv()

# --- GROQ ---
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL_ID  = os.getenv("GROQ_MODEL_ID", "llama-3.3-70b-versatile").strip()
TEMPERATURE    = float(os.getenv("TEMPERATURE", "0.1"))
MAX_TOKENS     = int(os.getenv("MAX_TOKENS", "800"))
GROQ_TIMEOUT   = float(os.getenv("GROQ_TIMEOUT", "60"))

# --- UI / OCR ---
APP_DARK_MODE  = True

OCR_LANG       = os.getenv("OCR_LANG", "spa+eng")  # español + inglés
OCR_PSM        = int(os.getenv("OCR_PSM", "6"))    # 6: bloque uniforme
OCR_DENOISE    = os.getenv("OCR_DENOISE", "1").strip() == "1"
