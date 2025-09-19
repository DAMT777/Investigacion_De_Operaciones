from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PIL import Image, ImageOps, ImageFilter

from config import OCR_LANG, OCR_PSM, OCR_DENOISE
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class OCRWorker(QThread):
    finished_ok = Signal(str)
    finished_error = Signal(str)

    def __init__(self, image_path: str) -> None:
        super().__init__()
        self.image_path = image_path

    def _preprocess(self, img: Image.Image) -> Image.Image:
        if OCR_DENOISE:
            img = ImageOps.grayscale(img)
            img = img.filter(ImageFilter.MedianFilter(size=3))
            img = ImageOps.autocontrast(img, cutoff=2)
        return img

    def run(self) -> None:
        try:
            img = Image.open(self.image_path)
            img = self._preprocess(img)
            config = f"--psm {OCR_PSM}"
            texto = pytesseract.image_to_string(img, lang=OCR_LANG, config=config)
            if not texto.strip():
                self.finished_error.emit("No se detectó texto en la imagen.")
                return
            self.finished_ok.emit(texto)
        except Exception as exc:  # noqa: BLE001
            self.finished_error.emit(str(exc))
