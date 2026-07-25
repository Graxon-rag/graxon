from .elevenlabs_processor import ElevenlabsAudioProcessor
from .assembly_processor import AssemblyAudioProcessor
from .deepgram_processor import DeepgramAudioProcessor
from .gladia_processor import GladiaAudioProcessor
from .groq_processor import GroqAduioProcessor
from .model import AudioProviderEnum
from .base import AudioProcessor


class AudioProcessorFactory:

    @staticmethod
    def get_processor(
            processor: AudioProviderEnum,
            file_path: str,
            filename: str,
            api_key: str,
            file_chunk_number: int,
            rag_chunk_start_index: int,
            timeout: float = 60 * 10,
            **kwargs
    ) -> AudioProcessor:

        segment_duration_min = kwargs.get("segment_duration_min", 10)
        max_time_per_rag_chunk_min = kwargs.get("max_time_per_rag_chunk_min", 2.0)
        max_words_per_rag_chunk = kwargs.get("max_words_per_rag_chunk", 300)

        if processor == AudioProviderEnum.ELEVENLABS:
            base_url = kwargs.get("base_url", "https://api.elevenlabs.io")
            model_id = kwargs.get("model_id", "scribe_v2")
            tag_audio_events = kwargs.get("tag_audio_events", True)
            diarize = kwargs.get("diarize", True)
            return ElevenlabsAudioProcessor(
                file_path=file_path,
                filename=filename,
                api_key=api_key,
                file_chunk_number=file_chunk_number,
                rag_chunk_start_index=rag_chunk_start_index,

                segment_duration_min=segment_duration_min,
                max_time_per_rag_chunk_min=max_time_per_rag_chunk_min,
                max_words_per_rag_chunk=max_words_per_rag_chunk,

                base_url=base_url,
                model_id=model_id,
                tag_audio_events=tag_audio_events,
                diarize=diarize,
                timeout=timeout
            )
        elif processor == AudioProviderEnum.ASSEMBLYAI:
            speaker_labels = kwargs.get("speaker_labels", True)
            language_detection = kwargs.get("language_detection", True)
            return AssemblyAudioProcessor(
                file_path=file_path,
                filename=filename,
                api_key=api_key,
                file_chunk_number=file_chunk_number,
                rag_chunk_start_index=rag_chunk_start_index,

                segment_duration_min=segment_duration_min,
                max_time_per_rag_chunk_min=max_time_per_rag_chunk_min,
                max_words_per_rag_chunk=max_words_per_rag_chunk,

                speaker_labels=speaker_labels,
                language_detection=language_detection,
            )
        elif processor == AudioProviderEnum.DEEPGRAM:
            model = kwargs.get("model", "nova-3")
            diarize = kwargs.get("diarize", True)
            smart_format = kwargs.get("smart_format", True)
            detect_language = kwargs.get("detect_language", True)
            return DeepgramAudioProcessor(
                file_path=file_path,
                filename=filename,
                api_key=api_key,
                file_chunk_number=file_chunk_number,
                rag_chunk_start_index=rag_chunk_start_index,

                segment_duration_min=segment_duration_min,
                max_time_per_rag_chunk_min=max_time_per_rag_chunk_min,
                max_words_per_rag_chunk=max_words_per_rag_chunk,

                model=model,
                diarize=diarize,
                smart_format=smart_format,
                detect_language=detect_language,
                timeout=timeout
            )
        elif processor == AudioProviderEnum.GLADIA:
            model = kwargs.get("model", "solaria-3")
            diarization = kwargs.get("diarization", True)
            return GladiaAudioProcessor(
                file_path=file_path,
                filename=filename,
                api_key=api_key,
                file_chunk_number=file_chunk_number,
                rag_chunk_start_index=rag_chunk_start_index,

                segment_duration_min=segment_duration_min,
                max_time_per_rag_chunk_min=max_time_per_rag_chunk_min,
                max_words_per_rag_chunk=max_words_per_rag_chunk,

                model=model,
                diarization=diarization,
                timeout=timeout
            )
        elif processor == AudioProviderEnum.GROQ:
            model = kwargs.get("model", "whisper-large-v3")
            return GroqAduioProcessor(
                file_path=file_path,
                filename=filename,
                api_key=api_key,
                file_chunk_number=file_chunk_number,
                rag_chunk_start_index=rag_chunk_start_index,

                segment_duration_min=segment_duration_min,
                max_time_per_rag_chunk_min=max_time_per_rag_chunk_min,
                max_words_per_rag_chunk=max_words_per_rag_chunk,

                model=model,
                timeout=timeout
            )
        else:
            raise ValueError(f"Unknown audio provider: {processor}")
