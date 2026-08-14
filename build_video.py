"""
장면 애니메이션 + 나레이션 -> out/ep01.mp4

각 장면은 [앞 1.4초 = 데이터가 그려지는 애니메이션] + [나머지 = 정지] 로 만든다.
정지 구간에 줌/패닝은 넣지 않는다 (차트 글씨가 뭉개진다).

  .venv/bin/python build_video.py             # 본편
  .venv/bin/python build_video.py --silent    # 오디오 없이 길이만 추정한 프리뷰
  .venv/bin/python build_video.py --theme light
  .venv/bin/python build_video.py --no-anim   # 애니메이션 없이 빠르게 (확인용)
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from narration import scenes
from render import BUILDERS, render

AUDIO = Path("out/audio")
WORK = Path("out/_segments")
FPS = 30
ANIM_SEC = 1.4      # 장면 도입 애니메이션 길이
SPEED = 0.95        # 숫자가 많아서 기본 속도는 빠르게 들린다
TAIL = 0.35
CPS = 5.5           # 무음 프리뷰용 한국어 초당 글자수


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        sys.exit(f"ffmpeg 실패:\n{' '.join(str(c) for c in cmd[:8])}...\n{p.stderr[-1500:]}")


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def anim_dir(stem, theme, i):
    """도입부 프레임들을 PNG 시퀀스로 렌더."""
    d = WORK / f"anim{i:02d}"
    d.mkdir(parents=True, exist_ok=True)
    n = int(ANIM_SEC * FPS)
    for k in range(n):
        render(stem, theme, (k + 1) / n, d / f"f{k:04d}.png")
    return d


def main() -> None:
    argv = sys.argv
    silent = "--silent" in argv
    no_anim = "--no-anim" in argv
    theme = "light" if "light" in argv else "dark"
    still_dir = Path("out/frames") / theme
    dest = Path("out") / ("ep01_preview.mp4" if silent else "ep01.mp4")

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)

    segs, total = [], 0.0
    for i, (stem, text, hold) in enumerate(scenes()):
        if stem not in BUILDERS:
            sys.exit(f"render.py 에 '{stem}' 장면이 없습니다")
        still = still_dir / f"{stem}.png"
        if not still.exists():
            sys.exit(f"프레임 없음: {still}  (render.py 를 먼저 돌리세요)")

        mp3 = AUDIO / f"{stem}.mp3"
        if not silent and not mp3.exists():
            sys.exit(f"오디오 없음: {mp3}  (render_audio.py 를 먼저 돌리세요)")

        dur = (len(text) / CPS if silent else duration(mp3) / SPEED) + hold + TAIL
        seg = WORK / f"{i:02d}.mp4"
        use_anim = not no_anim and dur > ANIM_SEC + 0.3

        cmd = ["ffmpeg", "-y", "-v", "error"]
        if use_anim:
            d = anim_dir(stem, theme, i)
            cmd += ["-framerate", str(FPS), "-i", str(d / "f%04d.png"),
                    "-loop", "1", "-framerate", str(FPS),
                    "-t", f"{dur - ANIM_SEC:.3f}", "-i", str(still)]
            vfilter = "[0:v][1:v]concat=n=2:v=1:a=0[v]"
            ai = 2
        else:
            cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}",
                    "-i", str(still)]
            vfilter = "[0:v]null[v]"
            ai = 1

        if silent:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            afilter = f"[{ai}:a]anull[a]"
        else:
            cmd += ["-i", str(mp3)]
            afilter = f"[{ai}:a]atempo={SPEED},apad,aresample=44100[a]"

        cmd += ["-filter_complex", f"{vfilter};{afilter}",
                "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "192k", str(seg)]
        run(cmd)

        segs.append(seg)
        total += dur
        print(f"  {stem:22s} {dur:5.1f}초{'  +anim' if use_anim else ''}")

    lst = WORK / "list.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(dest)])

    mb = dest.stat().st_size / 1_048_576
    print(f"\n-> {dest}  {int(total // 60)}분 {int(total % 60)}초  {mb:.1f}MB"
          + ("  (무음 프리뷰)" if silent else ""))


if __name__ == "__main__":
    main()
