from abc import ABC, abstractmethod


class SpeechToTextService(ABC):
    name: str

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError


class WhisperSpeechToTextService(SpeechToTextService):
    name = "Whisper"

    def __init__(self, model_size: str = "small") -> None:
        self.model_size = model_size

    def transcribe(self, audio_path: str) -> str:
        try:
            import whisper  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Whisper is not installed. Install it intentionally before enabling server-side STT."
            ) from exc

        model = whisper.load_model(self.model_size)
        result = model.transcribe(audio_path, fp16=False)
        return str(result["text"]).strip()


class XlsrSpeechToTextService(SpeechToTextService):
    name = "XLS-R"

    def transcribe(self, audio_path: str) -> str:
        raise RuntimeError("XLS-R adapter is ready, but a fine-tuned ASR checkpoint must be configured.")


class IndicConformerSpeechToTextService(SpeechToTextService):
    name = "IndicConformer"

    def transcribe(self, audio_path: str) -> str:
        raise RuntimeError("IndicConformer adapter is ready, but a supported checkpoint must be configured.")

