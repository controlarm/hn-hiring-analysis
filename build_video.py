"""
프레임 PNG + 나레이션 mp3 -> out/ep01.mp4

  .venv/bin/python build_video.py            # 오디오 있는 그대로 (본편)
  .venv/bin/python build_video.py --silent   # 오디오 없이 길이만 추정한 무음 프리뷰
  .venv/bin/python build_video.py --theme light

무음 프리뷰는 ElevenLabs 키 없이도 영상 흐름과 컷 길이를 먼저 볼 수 있게 하는 용도.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from narration import scenes

FRAMES = Path("out/frames")
AUDIO = Path("out/audio")
WORK = Path("out/_segments")
SPEED = 0.95        # 숫자가 많아서 기본 속도는 빠르게 들린다
TAIL = 0.35         # 컷마다 끝에 붙이는 여유
CPS = 5.5           # 무음 프리뷰용 한국어 초당 글자수 추정


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg 실패:\n{' '.join(cmd[:6])}...\n{p.stderr[-1500:]}")


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def main() -> None:
    silent = "--silent" in sys.argv
    theme = "light" if "--theme" in sys.argv and "light" in sys.argv else "dark"
    src = FRAMES / theme
    out_name = "ep01_preview.mp4" if silent else "ep01.mp4"

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    segments, total = [], 0.0
    for i, (stem, text, hold) in enumerate(scenes()):
        img = src / f"{stem}.png"
        if not img.exists():
            sys.exit(f"프레임 없음: {img}  (frames.py 를 먼저 돌리세요)")

        mp3 = AUDIO / f"{stem}.mp3"
        seg = WORK / f"{i:02d}.mp4"

        if silent or not mp3.exists():
            if not silent:
                sys.exit(f"오디오 없음: {mp3}  (render_audio.py 를 먼저 돌리세요)")
            dur = len(text) / CPS + hold + TAIL
            run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(img),
                 "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                 "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
                 "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                 str(seg)])
        else:
            dur = duration(mp3) / SPEED + hold + TAIL
            run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(img),
                 "-i", str(mp3),
                 "-filter_complex",
                 f"[1:a]atempo={SPEED},apad,aresample=44100[a]",
                 "-map", "0:v", "-map", "[a]", "-t", f"{dur:.3f}",
                 "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                 "-r", "30", "-c:a", "aac", "-b:a", "192k", str(seg)])

        segments.append(seg)
        total += dur
        print(f"  {stem:22s} {dur:5.1f}초")

    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segments))
    dest = Path("out") / out_name
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", str(dest)])

    mb = dest.stat().st_size / 1_048_576
    print(f"\n-> {dest}  {int(total // 60)}분 {int(total % 60)}초  {mb:.1f}MB"
          + ("  (무음 프리뷰)" if silent else ""))


if __name__ == "__main__":
    main()
