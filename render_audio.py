"""
narration.py -> ElevenLabs -> out/audio/*.mp3 (프레임별 1개)

준비:
  1. elevenlabs.io 가입 -> Voice Library 에서 목소리 선택 -> "Add to my voices"
  2. 그 목소리의 Voice ID 복사 (My Voices 에서 확인)
  3. Profile -> API Key 복사

실행:
  export ELEVENLABS_API_KEY="sk_..."
  export ELEVENLABS_VOICE_ID="..."
  .venv/bin/python render_audio.py            # 없는 것만 렌더
  .venv/bin/python render_audio.py --force    # 전부 다시

모델은 v3 아닌 multilingual v2. 숫자와 한국어 속 영어 발음이 v2가 더 안정적이다.
이미 렌더된 파일은 건너뛰므로, 대본 한 줄만 고쳤으면 그 mp3만 지우고 다시 돌리면 된다.
"""

import os
import sys
from pathlib import Path

import requests

from narration import CHECK_NUMBERS, scenes

OUT = Path("out/audio")
API = "https://api.elevenlabs.io/v1/text-to-speech"
MODEL = "eleven_multilingual_v2"

SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True,
}


def load_env(path=Path(".env")) -> None:
    """.env 를 읽어 환경변수로. 이미 있는 값은 덮지 않는다(셸 export 우선)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> None:
    load_env()
    key = os.environ.get("ELEVENLABS_API_KEY")
    voice = os.environ.get("ELEVENLABS_VOICE_ID")
    if not key or not voice:
        sys.exit(
            ".env 파일을 만들어 주세요 (.env.example 참고). git에는 올라가지 않습니다.\n"
            '  ELEVENLABS_API_KEY=sk_...\n'
            '  ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb'
        )

    force = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)

    for stem, text, _hold in scenes():
        dest = OUT / f"{stem}.mp3"
        if dest.exists() and not force:
            print(f"  skip  {stem}")
            continue

        r = requests.post(
            f"{API}/{voice}",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": text, "model_id": MODEL, "voice_settings": SETTINGS},
            params={"output_format": "mp3_44100_128"},
            timeout=180,
        )
        if r.status_code != 200:
            sys.exit(f"\n{stem} 실패 [{r.status_code}] {r.text[:400]}")

        dest.write_bytes(r.content)
        print(f"  ok    {stem}  {len(r.content) / 1024:.0f}KB")

    print(f"\n-> {OUT}")
    print("\n[반드시 귀로 확인] 아래 숫자가 제대로 읽히는지:")
    print("  " + ", ".join(CHECK_NUMBERS))
    print("  틀리면 narration.py 에서 해당 숫자를 한글로 풀어쓰고,")
    print("  그 mp3만 지운 뒤 다시 돌리세요.")


if __name__ == "__main__":
    main()
