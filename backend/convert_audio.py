import sys
from pathlib import Path

from pydub import AudioSegment

TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1
TARGET_SAMPLE_WIDTH = 2

INPUT_FILE = Path("test.wav")
OUTPUT_FILE = Path("test_16k.wav")


def convert_audio(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    audio = AudioSegment.from_file(input_path)
    audio = (
        audio.set_frame_rate(TARGET_SAMPLE_RATE)
        .set_channels(TARGET_CHANNELS)
        .set_sample_width(TARGET_SAMPLE_WIDTH)
    )

    audio.export(output_path, format="wav")


def main() -> int:
    try:
        convert_audio(INPUT_FILE, OUTPUT_FILE)
    except Exception as exc:
        print(f"[LỖI] Không thể chuyển đổi âm thanh: {exc}")
        return 1

    print(
        "[OK] Đã chuyển đổi âm thanh sang 16kHz mono 16-bit PCM: "
        f"{OUTPUT_FILE.resolve()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
