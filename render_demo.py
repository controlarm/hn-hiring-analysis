"""
도입부 30초 재설계 데모.

기존 파이프라인의 문제: 장면당 앞 1.4초만 애니메이션이고 나머지는 정지 이미지다.
196초 영상에서 움직이는 시간이 14초(7%)뿐이었다. 그래서 PPT 로 보인다.

이 렌더러는 다르게 만든다.
  - 장면을 3~4초짜리 '샷' 으로 쪼갠다 (20초에 한 번 -> 3초에 한 번)
  - 모든 프레임을 새로 그린다. 정지 구간이 없다
  - 나레이션 키워드가 말하는 시점에 화면에 뜬다
  - 숫자는 완성형으로 놓지 않고 세어 올라간다

usage:
  .venv/bin/python render_demo.py --probe   # 샷 경계 프레임만 (빠른 확인)
  .venv/bin/python render_demo.py           # 전체 프레임
"""

import math
import subprocess
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

from render import KR, THEMES, ease, fade

OUT = Path("out/frames_demo")
AUDIO = Path("out/audio_ep03")
FPS = 30
SPEED, TAIL = 0.95, 0.35          # build_video.py 와 같은 값
W, H, DPI = 16, 9, 120
T = THEMES["dark"]

# 장면별 샷 분할 가중치. 합이 1 이 되게 정규화한다
SHOTS = {
    "01_hook":  [("posting", 3.2), ("everywhere", 2.6), ("us_flip", 2.5),
                 ("dots", 3.6)],
    "02_twist": [("laws", 3.4), ("diverge", 2.8), ("real", 4.4)],
    "03_data":  [("accumulate", 3.3), ("count", 3.3), ("filter", 3.5)],
}


def dur(stem):
    d = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(AUDIO / f"{stem}.mp3")],
        capture_output=True, text=True).stdout.strip())
    return d / SPEED


def timeline():
    """(샷이름, 시작초, 끝초) 목록. 오디오 실측 길이에 맞춘다."""
    out, t = [], 0.0
    holds = {"01_hook": 0.3, "02_twist": 1.2, "03_data": 0.5}
    for stem, shots in SHOTS.items():
        span = dur(stem) + holds[stem] + TAIL
        total = sum(w for _, w in shots)
        for name, w in shots:
            out.append((name, t, t + span * w / total))
            t += span * w / total
    return out, t


# ───────────────────────────── 그리기 공통

def newfig():
    mpl.rcParams.update({"font.family": KR, "text.color": T["ink"]})
    fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor=T["surface"])
    return fig


def card(fig, x, y, w, h, alpha=1.0, fc=None, ec=None, lw=1.4, r=0.012):
    """공고 카드 한 장."""
    p = mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
        transform=fig.transFigure, facecolor=fc or T["grid"],
        edgecolor=ec or "none", linewidth=lw, alpha=alpha, zorder=2)
    fig.patches.append(p)
    return p


def bar(fig, x, y, w, h, alpha=1.0, c=None):
    fig.patches.append(mpatches.Rectangle(
        (x, y), w, h, transform=fig.transFigure,
        facecolor=c or T["ink3"], alpha=alpha, zorder=3))


def kinetic(fig, x, y, text, p, size=40, color=None, weight="bold",
            ha="left", delay=0.0, rise=0.02):
    """말하는 시점에 아래에서 살짝 올라오며 등장."""
    a = fade(p, delay, delay + 0.22)
    if a <= 0.02:
        return
    fig.text(x, y - rise * (1 - a), text, fontsize=size, ha=ha, va="center",
             color=color or T["ink"], fontweight=weight, alpha=a, zorder=6)


def countup(v, p, start=0.0, end=0.75):
    """0(또는 start값)에서 v 까지 세어 올라간다."""
    return v * ease(min(1.0, max(0.0, (p - start) / (end - start))))


# ───────────────────────────── 샷 10개

def s_posting(p):
    """익숙한 장면: 공고에 연봉이 '회사 내규에 따름'."""
    fig = newfig()
    a = ease(min(1, p / 0.25))
    card(fig, 0.28, 0.20, 0.44, 0.60, alpha=a, fc="#1e1d1b",
         ec=T["grid"], lw=1.6)
    rows = [("직무", "백엔드 개발자", 0.70), ("경력", "3년 이상", 0.615),
            ("지역", "서울 강남구", 0.53), ("고용형태", "정규직", 0.445)]
    for i, (k, v, y) in enumerate(rows):
        aa = fade(p, 0.10 + i * 0.055, 0.10 + i * 0.055 + 0.14)
        if aa <= 0.02:
            continue
        fig.text(0.325, y, k, fontsize=19, color=T["ink3"], va="center", alpha=aa)
        fig.text(0.455, y, v, fontsize=21, color=T["ink2"], va="center", alpha=aa)
    ab = fade(p, 0.40, 0.56)
    if ab > 0.02:
        fig.patches.append(mpatches.Rectangle(
            (0.305, 0.295), 0.39, 0.075, transform=fig.transFigure,
            facecolor=T["s2"], alpha=0.13 * ab, zorder=2))
        fig.text(0.325, 0.3325, "연봉", fontsize=19, color=T["ink3"],
                 va="center", alpha=ab)
        fig.text(0.455, 0.3325, "회사 내규에 따름", fontsize=23,
                 color=T["s2"], va="center", fontweight="bold", alpha=ab)
    return fig


def s_everywhere(p):
    """한 장이 아니라 전부 그렇다."""
    fig = newfig()
    cols, rows = 5, 3
    for i in range(cols * rows):
        cx, cy = i % cols, i // cols
        d = (cx + cy) * 0.035
        a = fade(p, d, d + 0.18) * 0.9
        if a <= 0.02:
            continue
        x = 0.055 + cx * 0.186
        y = 0.60 - cy * 0.215
        card(fig, x, y, 0.166, 0.175, alpha=a, fc="#1e1d1b", ec=T["grid"])
        bar(fig, x + 0.016, y + 0.128, 0.085, 0.011, a * 0.5)
        bar(fig, x + 0.016, y + 0.100, 0.120, 0.011, a * 0.35)
        fig.text(x + 0.016, y + 0.045, "회사 내규에 따름", fontsize=13.5,
                 color=T["s2"], alpha=a * 0.95, va="center")
    kinetic(fig, 0.5, 0.875, "당연하게 여기시죠", p, 46, T["ink"],
            ha="center", delay=0.45)
    return fig


def s_us_flip(p):
    """미국은 다르다."""
    fig = newfig()
    ao = 1 - ease(min(1, max(0, (p - 0.05) / 0.30)))
    if ao > 0.02:
        card(fig, 0.10, 0.30, 0.36, 0.40, alpha=ao * 0.8, fc="#1e1d1b",
             ec=T["grid"])
        fig.text(0.28, 0.50, "회사 내규에 따름", fontsize=22, color=T["s2"],
                 ha="center", va="center", alpha=ao)
        fig.text(0.28, 0.755, "한국", fontsize=20, color=T["ink3"],
                 ha="center", alpha=ao)
    an = ease(min(1, max(0, (p - 0.28) / 0.34)))
    if an > 0.02:
        card(fig, 0.54 - 0.03 * (1 - an), 0.30, 0.36, 0.40, alpha=an,
             fc="#1e1d1b", ec=T["s1"], lw=2.2)
        fig.text(0.72, 0.50, "$150,000 – $210,000", fontsize=27,
                 color=T["s1"], ha="center", va="center", fontweight="bold",
                 alpha=an)
        fig.text(0.72, 0.755, "미국", fontsize=20, color=T["ink3"],
                 ha="center", alpha=an)
    kinetic(fig, 0.5, 0.135, "그게 바뀌고 있습니다", p, 38, T["ink2"],
            ha="center", delay=0.62)
    return fig


def s_dots(p):
    """100칸 중 몇 칸. 1 -> 16 으로 채워진다."""
    fig = newfig()
    lit = countup(16, p, 0.18, 0.82)
    for i in range(100):
        cx, cy = i % 10, i // 10
        x = 0.325 + cx * 0.0355
        y = 0.700 - cy * 0.0555
        on = i < lit
        frac = 1.0 if i + 1 <= lit else max(0.0, lit - i)
        fig.patches.append(mpatches.FancyBboxPatch(
            (x, y), 0.0275, 0.043,
            boxstyle="round,pad=0,rounding_size=0.005",
            transform=fig.transFigure,
            facecolor=T["s2"] if on else T["grid"],
            alpha=(0.35 + 0.65 * frac) if on else 0.55, zorder=3))
    fig.text(0.5, 0.885, "연봉을 적은 공고", fontsize=22, color=T["ink3"],
             ha="center")
    n = int(round(lit))
    fig.text(0.5, 0.108, f"100곳 중 {max(1, n)}곳", fontsize=44,
             color=T["s2"] if n > 1 else T["ink2"], ha="center",
             fontweight="bold")
    a2 = fade(p, 0.30, 0.45)
    if a2 > 0.02:
        fig.text(0.5, 0.038, "2015년  →  2026년", fontsize=19,
                 color=T["ink3"], ha="center", alpha=a2)
    return fig


def s_laws(p):
    """법이 하나씩 생긴다."""
    fig = newfig()
    kinetic(fig, 0.5, 0.855, "급여 공개법", p, 44, T["ink"], ha="center")
    laws = [("콜로라도", "2021. 01"), ("뉴욕시", "2022. 11"),
            ("캘리포니아 · 워싱턴", "2023. 01")]
    for i, (place, when) in enumerate(laws):
        a = fade(p, 0.20 + i * 0.19, 0.20 + i * 0.19 + 0.20)
        if a <= 0.02:
            continue
        y = 0.585 - i * 0.175
        card(fig, 0.24, y, 0.52, 0.125, alpha=a, fc="#1e1d1b",
             ec=T["s1"] if i == 2 else T["grid"], lw=2.2 if i == 2 else 1.4)
        fig.text(0.275, y + 0.0625, place, fontsize=26, va="center",
                 color=T["ink"] if i == 2 else T["ink2"],
                 fontweight="bold", alpha=a)
        fig.text(0.725, y + 0.0625, when, fontsize=24, va="center", ha="right",
                 color=T["s1"] if i == 2 else T["ink3"], alpha=a)
    return fig


def s_diverge(p):
    """2023년에 갈라진다. 빠르게 그린다."""
    fig = newfig()
    d = pd.read_csv("data/ep03_salary.csv")
    us = d[d.region == "US"].groupby("year")["has"].mean() * 100
    no = d[d.region == "non-US"].groupby("year")["has"].mean() * 100
    ax = fig.add_axes([0.10, 0.16, 0.80, 0.60])
    ax.set_facecolor(T["surface"])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlim(2015, 2026); ax.set_ylim(0, 25)
    ax.set_xticks([2015, 2020, 2023, 2026])
    ax.tick_params(colors=T["ink3"], labelsize=15)
    ax.set_yticks([])
    e = ease(min(1, p / 0.72))
    n = max(2, int(len(us) * e))
    ax.plot(us.index[:n], us.values[:n], color=T["s2"], lw=5,
            solid_capstyle="round")
    ax.plot(no.index[:n], no.values[:n], color=T["s1"], lw=5,
            solid_capstyle="round")
    if us.index[n - 1] >= 2023:
        av = fade(p, 0.55, 0.72)
        ax.axvline(2023, color=T["ink3"], lw=1.6, ls=(0, (4, 4)), alpha=av * .8)
    if e > 0.55:
        ax.text(us.index[n - 1] + 0.12, us.values[n - 1], "미국", color=T["s2"],
                fontsize=22, fontweight="bold", va="center")
        ax.text(no.index[n - 1] + 0.12, no.values[n - 1], "미국 밖",
                color=T["s1"], fontsize=22, fontweight="bold", va="center")
    kinetic(fig, 0.10, 0.885, "데이터로 확인됩니다", p, 40, T["ink"], delay=0.05)
    return fig


def s_real(p):
    """+54% 에 줄을 긋고 +12% 로."""
    fig = newfig()
    fig.text(0.5, 0.80, "공개된 연봉, 10년간", fontsize=26, color=T["ink3"],
             ha="center")
    a1 = ease(min(1, p / 0.20))
    big = countup(54, p, 0.02, 0.30)
    y1 = 0.545
    fig.text(0.5, y1, f"+{int(round(big))}%", fontsize=112, color=T["ink"],
             ha="center", va="center", fontweight="bold", alpha=a1)
    cross = ease(min(1, max(0, (p - 0.36) / 0.16)))
    if cross > 0.01:
        fig.patches.append(mpatches.Rectangle(
            (0.5 - 0.115 * cross, y1 - 0.006), 0.23 * cross, 0.012,
            transform=fig.transFigure, facecolor=T["s2"], zorder=7))
    a2 = fade(p, 0.56, 0.74)
    if a2 > 0.02:
        small = countup(12, p, 0.58, 0.84)
        fig.text(0.5, 0.275, f"+{int(round(small))}%", fontsize=96,
                 color=T["s2"], ha="center", va="center", fontweight="bold",
                 alpha=a2)
        fig.text(0.5, 0.115, "물가를 빼면", fontsize=30, color=T["ink2"],
                 ha="center", alpha=a2)
    return fig


def s_accumulate(p):
    """공고가 쌓인다."""
    fig = newfig()
    cols, rows = 40, 18
    total = cols * rows
    shown = ease(min(1, p / 0.85)) * total
    for i in range(total):
        if i >= shown:
            break
        cx, cy = i % cols, i // cols
        fig.patches.append(mpatches.Rectangle(
            (0.085 + cx * 0.0208, 0.175 + cy * 0.0345), 0.015, 0.024,
            transform=fig.transFigure, facecolor=T["ink3"],
            alpha=0.42, zorder=3))
    kinetic(fig, 0.085, 0.885, "Hacker News  ·  Ask HN: Who is hiring?",
            p, 32, T["ink2"], weight="normal")
    return fig


def s_count(p):
    """80,854 까지 세어 올라간다."""
    fig = newfig()
    cols, rows = 40, 18
    for i in range(cols * rows):
        cx, cy = i % cols, i // cols
        fig.patches.append(mpatches.Rectangle(
            (0.085 + cx * 0.0208, 0.175 + cy * 0.0345), 0.015, 0.024,
            transform=fig.transFigure, facecolor=T["ink3"],
            alpha=0.30, zorder=3))
    fig.patches.append(mpatches.Rectangle(
        (0.0, 0.29), 1.0, 0.36, transform=fig.transFigure,
        facecolor=T["surface"], alpha=0.86, zorder=6))
    n = countup(80854, p, 0.05, 0.80)
    fig.text(0.5, 0.50, f"{int(n):,}", fontsize=124, color=T["ink"],
             ha="center", va="center", fontweight="bold", zorder=8)
    fig.text(0.5, 0.335, "2015년 이후 채용공고", fontsize=27, color=T["ink2"],
             ha="center", zorder=8)
    return fig


def s_filter(p):
    """연봉이 적힌 것만 남긴다."""
    fig = newfig()
    cols, rows = 40, 18
    total = cols * rows
    e = ease(min(1, max(0, (p - 0.10) / 0.60)))
    for i in range(total):
        cx, cy = i % cols, i // cols
        keep = (i * 7919) % 100 < 13          # 약 13% 가 연봉을 적었다
        c = T["s2"] if keep else T["ink3"]
        a = (0.42 + 0.55 * e) if keep else (0.42 - 0.36 * e)
        fig.patches.append(mpatches.Rectangle(
            (0.085 + cx * 0.0208, 0.175 + cy * 0.0345), 0.015, 0.024,
            transform=fig.transFigure, facecolor=c, alpha=a, zorder=3))
    kinetic(fig, 0.085, 0.885, "연봉이 적힌 공고만", p, 40, T["s2"], delay=0.30)
    return fig


DRAW = {"posting": s_posting, "everywhere": s_everywhere, "us_flip": s_us_flip,
        "dots": s_dots, "laws": s_laws, "diverge": s_diverge, "real": s_real,
        "accumulate": s_accumulate, "count": s_count, "filter": s_filter}


def main():
    tl, total = timeline()
    print(f"샷 {len(tl)}개 · 총 {total:.1f}초 · 평균 {total/len(tl):.1f}초/샷")
    for name, a, b in tl:
        print(f"  {a:5.1f}–{b:5.1f}  {name}")

    OUT.mkdir(parents=True, exist_ok=True)
    if "--probe" in sys.argv:
        for name, a, b in tl:
            for q in (0.35, 0.99):
                fig = DRAW[name](q)
                fig.savefig(OUT / f"probe_{name}_{int(q*100)}.png")
                plt.close(fig)
        print(f"-> {OUT}/probe_*.png")
        return

    n = int(total * FPS)
    for i in range(n):
        t = i / FPS
        name, a, b = next(s for s in tl if s[1] <= t < s[2]) if t < tl[-1][2] else tl[-1]
        fig = DRAW[name]((t - a) / (b - a))
        fig.savefig(OUT / f"f{i:05d}.png")
        plt.close(fig)
        if i % 60 == 0:
            print(f"  {i}/{n}  {t:5.1f}초  {name}")
    print(f"-> {n}프레임")


if __name__ == "__main__":
    main()
