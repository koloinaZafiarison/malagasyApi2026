"""import io
import os
from typing import Any, ClassVar, Optional, cast
import torch
import soundfile as sf
import gdown
from transformers import VitsModel, AutoTokenizer
from django.conf import settings

# Integration modele text to speech Malagasy
class MalagasyTTS:
    _instance: ClassVar[Optional["MalagasyTTS"]] = None
    device: str
    model: VitsModel
    tokenizer: Any
    sample_rate: int
    _MIN_MODEL_SIZE_BYTES: ClassVar[int] = 10 * 1024 * 1024

    def __new__(cls):
        if cls._instance is None:
            # Build a temporary instance first to avoid caching a half-initialized object.
            instance = cast("MalagasyTTS", super().__new__(cls))
            model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'tts')
            safetensors_path = os.path.join(model_path, 'model.safetensors')
            os.makedirs(model_path, exist_ok=True)

            file_id = '1l_OJ44pLv3s9rsL9wj-3MTj2_lOTlhJW'
            url = f'https://drive.google.com/uc?id={file_id}'

            def _download_model() -> None:
                print("Downloading model.safetensors from Google Drive...")
                downloaded_path = gdown.download(url, safetensors_path, quiet=False, fuzzy=True)
                if not downloaded_path or not os.path.exists(safetensors_path):
                    raise RuntimeError("Failed to download model.safetensors.")

            def _is_valid_model_file() -> bool:
                return os.path.exists(safetensors_path) and (
                    os.path.getsize(safetensors_path) >= cls._MIN_MODEL_SIZE_BYTES
                )

            # Download when missing.
            if not os.path.exists(safetensors_path):
                _download_model()

            # Retry once if file seems invalid (often Drive HTML/intermediate file).
            if not _is_valid_model_file():
                if os.path.exists(safetensors_path):
                    os.remove(safetensors_path)
                _download_model()

            if not _is_valid_model_file():
                size = os.path.getsize(safetensors_path) if os.path.exists(safetensors_path) else 0
                raise RuntimeError(
                    f"Invalid model.safetensors size ({size} bytes). "
                    "Verify Google Drive file access/link and retry."
                )

            instance.device = "cuda" if torch.cuda.is_available() else "cpu"
            instance.model = cast(VitsModel, VitsModel.from_pretrained(model_path))
            instance.model = cast(VitsModel, instance.model.to(instance.device))  # pyright: ignore[reportArgumentType]
            instance.tokenizer = AutoTokenizer.from_pretrained(model_path)
            instance.sample_rate = instance.model.config.sampling_rate
            cls._instance = instance

        return cast("MalagasyTTS", cls._instance)

    def synthesize(self, text: str) -> bytes:
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self.model(**inputs).waveform
        waveform = output.squeeze().cpu().numpy()
        buffer = io.BytesIO()
        sf.write(buffer, waveform, self.sample_rate, format='WAV')
        return buffer.getvalue()"""