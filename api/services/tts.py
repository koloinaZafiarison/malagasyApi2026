import io
import os
import torch
import soundfile as sf
import gdown
from transformers import VitsModel, AutoTokenizer
from django.conf import settings

class MalagasyTTS:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'tts')
            safetensors_path = os.path.join(model_path, 'model.safetensors')

            # Télécharger le fichier model.safetensors s'il n'existe pas
            if not os.path.exists(safetensors_path):
                print("📥 Téléchargement du fichier model.safetensors depuis Google Drive...")
                file_id = '1l_OJ44pLv3s9rsL9wj-3MTj2_lOTlhJW'
                url = f'https://drive.google.com/uc?id={file_id}'
                gdown.download(url, safetensors_path, quiet=False)
                print("✅ Téléchargement terminé")

            cls._instance.device = "cuda" if torch.cuda.is_available() else "cpu"
            cls._instance.model = VitsModel.from_pretrained(model_path).to(cls._instance.device)
            cls._instance.tokenizer = AutoTokenizer.from_pretrained(model_path)
            cls._instance.sample_rate = cls._instance.model.config.sampling_rate

        return cls._instance

    def synthesize(self, text: str) -> bytes:
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self.model(**inputs).waveform
        waveform = output.squeeze().cpu().numpy()
        buffer = io.BytesIO()
        sf.write(buffer, waveform, self.sample_rate, format='WAV')
        return buffer.getvalue()