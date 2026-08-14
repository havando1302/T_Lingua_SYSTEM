from collections import deque
import webrtcvad

from app.core.config import (
    BYTES_PER_SAMPLE,
    CHANNELS,
    SAMPLE_RATE,
    VAD_AGGRESSIVENESS,
    VAD_FRAME_MS,
    VAD_SILENCE_MS,
    VAD_SPEECH_PAD_MS
)


class WebRtcVadStream:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        sample_width: int = BYTES_PER_SAMPLE,
        frame_ms: int = VAD_FRAME_MS,
        aggressiveness: int = VAD_AGGRESSIVENESS,
        speech_pad_ms: int = VAD_SPEECH_PAD_MS,
        silence_ms: int = VAD_SILENCE_MS
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.frame_ms = frame_ms
        self._vad = webrtcvad.Vad(aggressiveness)

        self._frame_bytes = int(
            self.sample_rate * self.frame_ms / 1000
        ) * self.sample_width * self.channels

        self._prepad_frames = max(1, speech_pad_ms // self.frame_ms)
        self._max_silence_frames = max(1, silence_ms // self.frame_ms)

        self._residual = b""
        self._ring = deque(maxlen=self._prepad_frames)
        self._current = bytearray()
        self._in_speech = False
        self._silence_frames = 0

    def process(self, audio_bytes: bytes) -> tuple[list[bytes], bytes, bool]:
        """
        Returns (final_utterances, current_buffer, in_speech).
        final_utterances is a list of completed utterance buffers.
        current_buffer contains the in-progress utterance audio.
        """
        if not audio_bytes:
            return [], bytes(self._current), self._in_speech

        data = self._residual + audio_bytes
        offset = 0
        finals: list[bytes] = []

        while len(data) - offset >= self._frame_bytes:
            frame = data[offset:offset + self._frame_bytes]
            offset += self._frame_bytes

            is_speech = self._vad.is_speech(frame, self.sample_rate)

            if not self._in_speech:
                self._ring.append(frame)
                if is_speech:
                    self._in_speech = True
                    self._current.extend(b"".join(self._ring))
                    self._ring.clear()
                    self._silence_frames = 0
            else:
                self._current.extend(frame)
                if is_speech:
                    self._silence_frames = 0
                else:
                    self._silence_frames += 1
                    if self._silence_frames >= self._max_silence_frames:
                        finals.append(bytes(self._current))
                        self._current.clear()
                        self._in_speech = False
                        self._silence_frames = 0

        self._residual = data[offset:]

        return finals, bytes(self._current), self._in_speech