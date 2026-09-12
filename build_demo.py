"""
30초 데모 합성. 프레임 시퀀스 + 나레이션 + 사운드.

기존 build_video.py 와 다른 점
  - 장면 단위 정지화면이 아니라 연속 프레임 시퀀스를 그대로 쓴다
  - 나레이션만 있던 것에 저음 드론과 컷 전환음을 얹는다
    (지금은 목소리만 있어서 정지화면과 겹쳐 더 휑하게 들린다)

드론은 '음악' 이라기보다 룸톤에 가깝게 아주 작게 깐다.
어설픈 배경음악은 없느니만 못하므로 존재감을 일부러 낮췄다.

usage: .venv/bin/python build_demo.py
"""

import subprocess
from pathlib import Path

from render_demo import AUDIO, FPS, SPEED, TAIL, timeline

WORK = Path("out/_demo")
FRAMES = Path("out/frames_demo")
OUT = Path("out/demo30.mp4")
HOLDS = {"01_hook": 0.3, "02_twist": 1.2, "03_data": 0.5}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"ffmpeg 실패:\n{' '.join(map(str, cmd))}\n{r.stderr[-1500:]}")


def probe(p):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


def voice_track(total):
    """장면별 mp3 를 실제 시작 시각에 맞춰 한 트랙으로."""
    parts = []
    for stem in HOLDS:
        src = AUDIO / f"{stem}.mp3"
        d = probe(src) / SPEED + HOLDS[stem] + TAIL
        seg = WORK / f"v_{stem}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
             "-af", f"atempo={SPEED},apad,aresample=48000",
             "-t", f"{d:.3f}", "-ac", "2", str(seg)])
        parts.append(seg)
    lst = WORK / "voice.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    out = WORK / "voice.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(out)])
    return out


def bed_track(total, cuts):
    """저음 드론 + 컷마다 짧은 전환음."""
    d = f"{total:.2f}"
    inputs, mixes = [], []
    # 드론: 낮은 3화음을 아주 작게. 순음만 쓰면 시험음처럼 들리므로
    # 브라운 노이즈를 로우패스해 같이 깐다
    for f, v in [(65.41, 0.055), (98.00, 0.032), (130.81, 0.020)]:
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={f}:duration={d}"]
        mixes.append(f"volume={v}")
    inputs += ["-f", "lavfi", "-i", f"anoisesrc=color=brown:duration={d}"]
    mixes.append("lowpass=f=180,volume=0.030")

    fc = []
    for i, m in enumerate(mixes):
        fc.append(f"[{i}:a]{m}[d{i}]")
    fc.append(f"{''.join(f'[d{i}]' for i in range(len(mixes)))}"
              f"amix=inputs={len(mixes)}:normalize=0,"
              f"tremolo=f=0.12:d=0.35,"
              f"afade=t=in:d=1.2,afade=t=out:st={total-1.4:.2f}:d=1.4[bed]")

    # 컷 전환음: 짧은 핑크노이즈 버스트
    n = len(mixes)
    tags = ["[bed]"]
    for j, c in enumerate(cuts):
        inputs += ["-f", "lavfi", "-i", "anoisesrc=color=pink:duration=0.45"]
        idx = n + j
        fc.append(f"[{idx}:a]highpass=f=400,lowpass=f=5000,"
                  f"afade=t=in:d=0.04,afade=t=out:st=0.06:d=0.34,"
                  f"volume=0.16,adelay={int(c*1000)}|{int(c*1000)}[w{j}]")
        tags.append(f"[w{j}]")
    fc.append(f"{''.join(tags)}amix=inputs={len(tags)}:normalize=0:duration=first,"
              f"aresample=48000[bedout]")

    out = WORK / "bed.wav"
    run(["ffmpeg", "-y", "-v", "error", *inputs,
         "-filter_complex", ";".join(fc), "-map", "[bedout]",
         "-t", d, "-ac", "2", str(out)])
    return out


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    tl, total = timeline()
    frames = sorted(FRAMES.glob("f*.png"))
    if not frames:
        raise SystemExit("프레임이 없습니다. render_demo.py 를 먼저 돌리세요")
    print(f"프레임 {len(frames)}장 · {total:.1f}초 · 샷 {len(tl)}개")

    voice = voice_track(total)
    cuts = [a for _, a, _ in tl[1:]]          # 첫 샷 시작에는 전환음 없음
    bed = bed_track(total, cuts)

    run(["ffmpeg", "-y", "-v", "error",
         "-framerate", str(FPS), "-i", str(FRAMES / "f%05d.png"),
         "-i", str(voice), "-i", str(bed),
         "-filter_complex",
         "[1:a]volume=1.0[v1];[2:a]volume=1.0[v2];"
         "[v1][v2]amix=inputs=2:normalize=0:duration=first,"
         "alimiter=limit=0.95,aresample=48000[a]",
         "-map", "0:v", "-map", "[a]",
         "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", str(OUT)])

    mb = OUT.stat().st_size / 1e6
    print(f"-> {OUT}  {total:.1f}초  {mb:.1f}MB")


if __name__ == "__main__":
    main()
