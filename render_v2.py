"""
3편 v2 렌더러. 전체 196초를 샷 52개로 다시 만든다.

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

from ep03_analyze import band, region          # noqa: F401  (경계분석이 쓴다)
from render import KR, THEMES, ease, fade
from render_ep03 import did_bounds

OUT = Path("out/frames_v2")
AUDIO = Path("out/audio_ep03")
FPS = 30
SPEED, TAIL = 0.95, 0.35          # build_video.py 와 같은 값
W, H, DPI = 16, 9, 120
T = THEMES["dark"]

# 장면별 샷 분할 가중치. 합이 1 이 되게 정규화한다.
# 도입부는 3초대로 빠르게, 분석부는 4초대로 조금 숨을 준다.
SHOTS = {
    "01_hook":  [("posting", 3.2), ("everywhere", 2.6), ("us_flip", 2.5),
                 ("dots", 3.6)],
    "02_twist": [("laws", 3.4), ("diverge", 2.8), ("real", 4.4)],
    "03_data":  [("accumulate", 3.3), ("count", 3.3), ("filter", 3.5)],
    "04_control": [("cant_say", 3.6), ("alt_reasons", 4.0), ("need_control", 3.0),
                   ("treat_def", 3.7), ("ctrl_def", 3.7), ("law_applies", 3.5)],
    "05_jump":  [("j_pre", 4.0), ("j_2023", 4.4), ("j_law", 4.0),
                 ("j_ctrl", 4.0), ("j_now", 4.2)],
    "06_robust": [("stop", 3.2), ("discarded", 4.2), ("not_free", 3.4),
                  ("bound_us", 4.4), ("bound_non", 4.2), ("bound_all", 6.2)],
    "07_avoid": [("suspect", 3.4), ("game_it", 4.4), ("width_line", 4.4),
                 ("width_cmp", 4.4), ("no_evidence", 3.8)],
    "08_real":  [("good_news", 3.2), ("nominal", 4.0), ("cpi", 3.8),
                 ("subtract", 4.0), ("left", 3.4)],
    "09_limits": [("l_head", 3.2), ("l1a", 4.2), ("l1b", 4.2), ("l1c", 4.6),
                  ("l2a", 4.2), ("l2b", 4.4), ("l3a", 4.4), ("l3b", 5.6)],
    "10_summary": [("s_head", 2.8), ("s1", 3.8), ("s2", 3.8), ("s3", 4.2),
                   ("s_line", 4.4), ("s_repo", 3.3)],
}

HOLDS = {"01_hook": 0.3, "02_twist": 1.2, "03_data": 0.5, "04_control": 0.6,
         "05_jump": 0.8, "06_robust": 0.8, "07_avoid": 0.8, "08_real": 2.8,
         "09_limits": 1.0, "10_summary": 1.5}


def dur(stem):
    d = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(AUDIO / f"{stem}.mp3")],
        capture_output=True, text=True).stdout.strip())
    return d / SPEED


def timeline():
    """(샷이름, 시작초, 끝초) 목록. 오디오 실측 길이에 맞춘다."""
    out, t = [], 0.0
    for stem, shots in SHOTS.items():
        span = dur(stem) + HOLDS[stem] + TAIL
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


# ───────────────────────────── 재사용 프리미티브
# 샷이 52개라 매번 새로 그리면 코드가 감당이 안 된다.
# 아래 넷으로 대부분을 조립한다.

def stmt(p, lines, size=44, gap=0.115, y=None, accent=None, sub=None):
    """문장 몇 줄을 화면 가운데. 한 줄씩 시차를 두고 올라온다."""
    fig = newfig()
    n = len(lines)
    y0 = (0.5 + (n - 1) * gap / 2) if y is None else y
    for i, line in enumerate(lines):
        c = T["s2"] if (accent is not None and i in
                        (accent if isinstance(accent, (list, tuple)) else [accent])) \
            else T["ink"]
        kinetic(fig, 0.5, y0 - i * gap, line, p, size, c, ha="center",
                delay=0.04 + i * 0.16)
    if sub:
        kinetic(fig, 0.5, y0 - n * gap - 0.045, sub, p, 25, T["ink3"],
                weight="normal", ha="center", delay=0.10 + n * 0.16)
    return fig


def dotgrid(fig, x0, y0, lit, total=100, cols=10, cell=0.0275, ch=0.043,
            gap=0.008, on=None, off=None, alpha_on=1.0):
    """N칸 중 lit칸이 켜진 격자."""
    on, off = on or T["s2"], off or T["grid"]
    for i in range(total):
        cx, cy = i % cols, i // cols
        frac = 1.0 if i + 1 <= lit else max(0.0, lit - i)
        fig.patches.append(mpatches.FancyBboxPatch(
            (x0 + cx * (cell + gap), y0 - cy * (ch + gap * 1.6)), cell, ch,
            boxstyle="round,pad=0,rounding_size=0.005",
            transform=fig.transFigure,
            facecolor=on if frac > 0 else off,
            alpha=(0.35 + 0.65 * frac) * alpha_on if frac > 0 else 0.5,
            zorder=3))


def hbars(fig, p, rows, xmax, caption=None, x0=0.085, y0=0.60, step=0.155,
          h=0.058, fmt="{:+.1f}%p", stagger=0.14):
    """가로 막대 몇 개가 차례로 자란다."""
    for i, (name, val, c) in enumerate(rows):
        grow = ease(min(1.0, max(0.0, (p - i * stagger) / 0.52)))
        y = y0 - i * step
        fig.text(x0, y + h + 0.028, name, fontsize=21, color=T["ink"],
                 fontweight="bold", va="bottom")
        fig.patches.append(mpatches.Rectangle(
            (x0, y), 0.78 * (val / xmax) * grow, h, transform=fig.transFigure,
            facecolor=c, zorder=3))
        if grow > 0.80:
            fig.text(x0 + 0.78 * (val / xmax) * grow + 0.014, y + h / 2,
                     fmt.format(val), fontsize=25, color=c, va="center",
                     fontweight="bold", alpha=fade(p, i * stagger + 0.42))
    if caption:
        fig.text(x0, y0 - (len(rows) - 1) * step - 0.075, caption,
                 fontsize=16, color=T["ink3"])


def band_bar(fig, lo, hi, y, tag, color, grow=1.0, xmin=80, xmax=430):
    """연봉 범위를 가로 띠 하나로. 폭 비교용."""
    f = lambda v: 0.085 + 0.80 * (v - xmin) / (xmax - xmin)
    x1, x2 = f(lo), f(lo + (hi - lo) * grow)
    fig.patches.append(mpatches.FancyBboxPatch(
        (x1, y), max(0.002, x2 - x1), 0.070,
        boxstyle="round,pad=0,rounding_size=0.010",
        transform=fig.transFigure, facecolor=color, alpha=0.90, zorder=3))
    fig.text(0.085, y + 0.104, tag, fontsize=20, color=T["ink2"], va="bottom")
    if grow > 0.85:
        fig.text(x1, y - 0.038, f"${lo}k", fontsize=18, color=T["ink3"],
                 ha="center")
        fig.text(x2, y - 0.038, f"${hi}k", fontsize=18, color=T["ink3"],
                 ha="center")


def diverge_chart(p, upto=2026, reveal=1.0, focus=None, law=False,
                  head=None, note=None):
    """미국 vs 미국 밖 공개율. 여러 샷이 단계별로 재사용한다."""
    fig = newfig()
    d = pd.read_csv("data/ep03_salary.csv")
    us = d[d.region == "US"].groupby("year")["has"].mean() * 100
    no = d[d.region == "non-US"].groupby("year")["has"].mean() * 100
    us, no = us[us.index <= upto], no[no.index <= upto]
    ax = fig.add_axes([0.10, 0.17, 0.80, 0.56])
    ax.set_facecolor(T["surface"])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlim(2015, 2026); ax.set_ylim(0, 25)
    ax.set_xticks([2015, 2018, 2021, 2023, 2026])
    ax.tick_params(colors=T["ink3"], labelsize=15)
    ax.set_yticks([])
    e = reveal if reveal < 1 else ease(min(1, p / 0.62)) if upto < 2026 else 1.0
    n = max(2, int(len(us) * e))
    for key, ser, lab, c in [("us", us, "미국", T["s2"]),
                             ("no", no, "미국 밖", T["s1"])]:
        dim = focus is not None and key != focus
        ax.plot(ser.index[:n], ser.values[:n], color=c, lw=5,
                solid_capstyle="round", alpha=0.22 if dim else 1)
        if n >= 3:
            ax.text(ser.index[n - 1] + 0.12, ser.values[n - 1], lab, color=c,
                    fontsize=21, fontweight="bold", va="center",
                    alpha=0.22 if dim else 1)
    if law:
        a = fade(p, 0.10, 0.32)
        ax.axvline(2023, color=T["ink3"], lw=1.8, ls=(0, (4, 4)), alpha=a * .85)
        ax.text(2022.85, 23.6, "캘리포니아·워싱턴\n급여 공개법", ha="right",
                va="top", fontsize=15, color=T["ink2"], alpha=a)
    if head:
        kinetic(fig, 0.10, 0.885, head, p, 40, T["ink"])
    if note:
        kinetic(fig, 0.10, 0.075, note, p, 26, T["s2"], weight="normal",
                delay=0.40)
    return fig


# ───────────────────────────── 샷: 도입부

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


# ───────────────────────────── 샷: 04 대조군 설계

def s_cant_say(p):
    fig = diverge_chart(p, focus="us", head="공개가 늘었다")
    kinetic(fig, 0.10, 0.075, "그런데 법 때문이라고 말할 수 있나", p, 30,
            T["ink2"], weight="normal", delay=0.45)
    return fig


def s_alt_reasons(p):
    """다른 설명들도 같은 그림을 만든다."""
    fig = newfig()
    kinetic(fig, 0.5, 0.845, "같은 그림을 만드는 다른 이유들", p, 36, T["ink2"],
            weight="normal", ha="center")
    for i, txt in enumerate(["경기가 좋아졌다", "관행이 바뀌었다",
                             "채용 경쟁이 심해졌다"]):
        a = fade(p, 0.16 + i * 0.20, 0.16 + i * 0.20 + 0.20)
        if a <= 0.02:
            continue
        y = 0.575 - i * 0.165
        card(fig, 0.235, y, 0.53, 0.118, alpha=a, fc="#1e1d1b", ec=T["grid"])
        fig.text(0.5, y + 0.059, txt, fontsize=27, ha="center", va="center",
                 color=T["ink2"], alpha=a)
    return fig


def s_need_control(p):
    return stmt(p, ["그래서 대조군을 만들었습니다"], size=48)


def s_treat_def(p):
    """처치군: 미국만 적힌 공고."""
    fig = newfig()
    kinetic(fig, 0.5, 0.845, "처치군", p, 34, T["s2"], ha="center")
    a = ease(min(1, p / 0.30))
    card(fig, 0.26, 0.30, 0.48, 0.44, alpha=a, fc="#1e1d1b", ec=T["s2"], lw=2.2)
    for i, (k, v) in enumerate([("지역", "San Francisco, CA"),
                                ("", "New York, NY"), ("", "Seattle, WA")]):
        aa = fade(p, 0.22 + i * 0.13, 0.22 + i * 0.13 + 0.16)
        if aa <= 0.02:
            continue
        fig.text(0.30, 0.645 - i * 0.098, k, fontsize=18, color=T["ink3"],
                 va="center", alpha=aa)
        fig.text(0.40, 0.645 - i * 0.098, v, fontsize=24, color=T["ink"],
                 va="center", alpha=aa)
    kinetic(fig, 0.5, 0.355, "미국 지역만 적힌 공고", p, 25, T["ink2"],
            weight="normal", ha="center", delay=0.62)
    kinetic(fig, 0.5, 0.135, "법이 적용된다", p, 30, T["s2"], ha="center",
            delay=0.74)
    return fig


def s_ctrl_def(p):
    """대조군: 미국 밖만 적힌 공고."""
    fig = newfig()
    kinetic(fig, 0.5, 0.845, "대조군", p, 34, T["s1"], ha="center")
    a = ease(min(1, p / 0.30))
    card(fig, 0.26, 0.30, 0.48, 0.44, alpha=a, fc="#1e1d1b", ec=T["s1"], lw=2.2)
    for i, (k, v) in enumerate([("지역", "London, UK"),
                                ("", "Berlin, Germany"), ("", "Toronto, Canada")]):
        aa = fade(p, 0.22 + i * 0.13, 0.22 + i * 0.13 + 0.16)
        if aa <= 0.02:
            continue
        fig.text(0.30, 0.645 - i * 0.098, k, fontsize=18, color=T["ink3"],
                 va="center", alpha=aa)
        fig.text(0.40, 0.645 - i * 0.098, v, fontsize=24, color=T["ink"],
                 va="center", alpha=aa)
    kinetic(fig, 0.5, 0.355, "미국이 아닌 곳만 적힌 공고", p, 25, T["ink2"],
            weight="normal", ha="center", delay=0.62)
    kinetic(fig, 0.5, 0.135, "법이 적용되지 않는다", p, 30, T["s1"], ha="center",
            delay=0.74)
    return fig


def s_law_applies(p):
    """섞인 공고는 버린다."""
    fig = newfig()
    kinetic(fig, 0.5, 0.855, "둘 다 적혔거나 못 찾은 공고는", p, 34, T["ink2"],
            weight="normal", ha="center")
    a = ease(min(1, max(0, (p - 0.18) / 0.32)))
    card(fig, 0.28, 0.455, 0.44, 0.145, alpha=a * 0.75, fc="#1e1d1b",
         ec=T["grid"])
    fig.text(0.5, 0.5275, "San Francisco / London", fontsize=25,
             color=T["ink2"], ha="center", va="center", alpha=a)
    cross = ease(min(1, max(0, (p - 0.44) / 0.20)))
    if cross > 0.01:
        for d in (1, -1):
            fig.patches.append(mpatches.Rectangle(
                (0.5 - 0.145 * cross, 0.5275 - 0.004), 0.29 * cross, 0.008,
                transform=fig.transFigure, facecolor=T["s2"], zorder=7,
                angle=d * 7, rotation_point=(0.5, 0.5275)))
    kinetic(fig, 0.5, 0.20, "버렸습니다", p, 46, T["s2"], ha="center", delay=0.60)
    kinetic(fig, 0.5, 0.095, "섞이면 대조군이 아니다", p, 24, T["ink3"],
            weight="normal", ha="center", delay=0.74)
    return fig


# ───────────────────────────── 샷: 05 급등

def s_j_pre(p):
    return diverge_chart(p, upto=2022, head="2022년까지는 둘 다 낮았다")


def s_j_2023(p):
    fig = diverge_chart(p, upto=2023, reveal=1.0, head="2023년")
    a = fade(p, 0.25, 0.48)
    if a > 0.02:
        fig.text(0.72, 0.50, "두 배", fontsize=86, color=T["s2"], ha="center",
                 va="center", fontweight="bold", alpha=a)
        fig.text(0.72, 0.395, "미국만", fontsize=24, color=T["ink2"],
                 ha="center", alpha=a)
    return fig


def s_j_law(p):
    return diverge_chart(p, upto=2023, law=True,
                         head="그해 1월, 법이 시행됐다")


def s_j_ctrl(p):
    return diverge_chart(p, upto=2023, focus="no", law=True,
                         head="같은 해 대조군은 내려갔다",
                         note="1.4%  →  0.9%")


def s_j_now(p):
    """다섯 곳 중 한 곳 vs 스물다섯 곳 중 한 곳."""
    fig = newfig()
    kinetic(fig, 0.5, 0.885, "지금", p, 34, T["ink2"], weight="normal",
            ha="center")
    for i, (tag, lit, c, x0) in enumerate(
            [("미국", 20, T["s2"], 0.075), ("미국 밖", 4, T["s1"], 0.545)]):
        a = fade(p, 0.10 + i * 0.22, 0.10 + i * 0.22 + 0.20)
        if a <= 0.02:
            continue
        grow = countup(lit, p, 0.16 + i * 0.22, 0.72 + i * 0.14)
        dotgrid(fig, x0, 0.640, grow, total=100, cols=10, cell=0.0255,
                ch=0.038, gap=0.0075, on=c, alpha_on=a)
        fig.text(x0 + 0.163, 0.735, tag, fontsize=27, color=c, ha="center",
                 fontweight="bold", alpha=a)
        n = max(1, int(round(grow)))
        fig.text(x0 + 0.163, 0.115, f"100곳 중 {n}곳", fontsize=31, color=c,
                 ha="center", fontweight="bold", alpha=a)
    return fig


# ───────────────────────────── 샷: 06 경계 분석

def s_stop(p):
    return stmt(p, ["여기서 멈추면 안 됩니다"], size=48)


def s_discarded(p):
    """전체 중 31%를 버렸다."""
    fig = newfig()
    kinetic(fig, 0.5, 0.885, "지역을 판정하지 못한 공고", p, 32, T["ink2"],
            weight="normal", ha="center")
    lit = countup(31, p, 0.14, 0.74)
    dotgrid(fig, 0.325, 0.700, lit, total=100, cols=10, on=T["ink"],
            off=T["grid"])
    n = int(round(lit))
    fig.text(0.5, 0.108, f"100건 중 {max(1, n)}건", fontsize=42, color=T["ink"],
             ha="center", fontweight="bold")
    kinetic(fig, 0.5, 0.038, "버렸습니다", p, 25, T["s2"], ha="center", delay=0.66)
    return fig


def s_not_free(p):
    return stmt(p, ["버리는 건", "공짜가 아닙니다"], size=48, accent=1)


def s_bound_us(p):
    obs, lo, hi = did_bounds()
    fig = newfig()
    kinetic(fig, 0.085, 0.885, "버린 것이 전부 미국이었다면", p, 38, T["ink"])
    hbars(fig, p, [("실제 분류", obs, T["s2"]),
                   ("전부 미국이라 가정", hi, T["ink3"])], 12.5,
          caption="미국이 미국 밖보다 더 오른 정도 (차이의 차이)",
          y0=0.545, step=0.215)
    return fig


def s_bound_non(p):
    obs, lo, hi = did_bounds()
    fig = newfig()
    kinetic(fig, 0.085, 0.885, "전부 미국 밖이었다면", p, 38, T["ink"])
    hbars(fig, p, [("실제 분류", obs, T["s2"]),
                   ("전부 미국 밖이라 가정", lo, T["ink3"])], 12.5,
          caption="미국이 미국 밖보다 더 오른 정도 (차이의 차이)",
          y0=0.545, step=0.215)
    return fig


def s_bound_all(p):
    obs, lo, hi = did_bounds()
    fig = newfig()
    kinetic(fig, 0.085, 0.905, "어느 극단을 넣어도 방향은 같았다", p, 40, T["ink"])
    hbars(fig, p, [("실제 분류", obs, T["s2"]),
                   ("전부 미국이라 가정", hi, T["s1"]),
                   ("전부 미국 밖이라 가정", lo, T["s1"])], 12.5,
          y0=0.615, step=0.185, stagger=0.11)
    kinetic(fig, 0.085, 0.105, "결론이 분류 방식에 기대고 있지 않다는 뜻", p, 26,
            T["ink2"], weight="normal", delay=0.62)
    return fig


# ───────────────────────────── 샷: 07 회피 가설

def s_suspect(p):
    return stmt(p, ["다음 의심입니다"], size=48)


def s_game_it(p):
    """법을 지키는 척 범위를 넓게 쓰면?"""
    fig = newfig()
    kinetic(fig, 0.085, 0.885, "범위를 아주 넓게 쓰면 되지 않나", p, 38, T["ink"])
    grow = ease(min(1, max(0, (p - 0.16) / 0.52)))
    band_bar(fig, 100, 400, 0.455, "이렇게 쓰면 법은 지킨 셈", T["ink3"], grow)
    kinetic(fig, 0.085, 0.235, "정보는 사실상 없다", p, 30, T["s2"], delay=0.70)
    return fig


def s_width_line(p):
    """실제 폭 시계열."""
    r = pd.read_csv("data/ep03_real.csv")
    r = r[r.year >= 2016]
    fig = newfig()
    kinetic(fig, 0.085, 0.885, "그것도 세어봤습니다", p, 38, T["ink"])
    ax = fig.add_axes([0.10, 0.17, 0.80, 0.55])
    ax.set_facecolor(T["surface"])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlim(2016, 2026); ax.set_ylim(0, 60)
    ax.set_xticks([2016, 2019, 2022, 2026])
    ax.tick_params(colors=T["ink3"], labelsize=15)
    ax.set_yticks([])
    e = ease(min(1, p / 0.68))
    n = max(2, int(len(r) * e))
    ax.plot(r.year.values[:n], r["width_%"].values[:n], color=T["s1"], lw=5,
            solid_capstyle="round")
    ax.text(r.year.values[n - 1] + 0.12, r["width_%"].values[n - 1], "밴드 폭",
            color=T["s1"], fontsize=20, fontweight="bold", va="center")
    kinetic(fig, 0.085, 0.075, "오히려 좁아졌습니다", p, 30, T["s1"],
            weight="normal", delay=0.62)
    return fig


def s_width_cmp(p):
    """2016 vs 2026 폭 비교.

    달러 폭으로 그리면 $59k 대 $56k 라 거의 같아 보인다.
    좁아진 것은 하한 대비 비율이므로, 하한을 같은 자리에 맞추고
    거기서 상한까지 뻗은 길이로 그린다. 그래야 화면이 나레이션과 어긋나지 않는다.
    """
    fig = newfig()
    kinetic(fig, 0.085, 0.895, "하한에서 상한까지, 하한 대비 몇 %인가", p, 34,
            T["ink"])
    rows = [("2016년", 49, "$120k", "$179k", T["ink3"]),
            ("2026년", 38, "$150k", "$206k", T["s1"])]
    for i, (yr, w, lo, hi, c) in enumerate(rows):
        grow = ease(min(1.0, max(0.0, (p - 0.12 - i * 0.24) / 0.46)))
        y = 0.560 - i * 0.250
        fig.text(0.085, y + 0.098, yr, fontsize=23, color=T["ink2"], va="bottom")
        # 하한 지점 표시. 둘 다 같은 x 에서 출발한다
        fig.patches.append(mpatches.Rectangle(
            (0.085, y - 0.020), 0.004, 0.112, transform=fig.transFigure,
            facecolor=T["ink3"], alpha=0.7, zorder=4))
        fig.patches.append(mpatches.FancyBboxPatch(
            (0.089, y), max(0.002, 0.0148 * w * grow), 0.072,
            boxstyle="round,pad=0,rounding_size=0.008",
            transform=fig.transFigure, facecolor=c, alpha=0.92, zorder=3))
        fig.text(0.085, y - 0.052, lo, fontsize=17, color=T["ink3"])
        if grow > 0.82:
            a = fade(p, 0.12 + i * 0.24 + 0.36)
            fig.text(0.089 + 0.0148 * w * grow + 0.016, y + 0.036,
                     f"+{w}%", fontsize=30, color=c, va="center",
                     fontweight="bold", alpha=a)
            fig.text(0.089 + 0.0148 * w * grow, y - 0.052, hi, fontsize=17,
                     color=T["ink3"], ha="center", alpha=a)
    return fig


def s_no_evidence(p):
    return stmt(p, ["피하고 있다는", "증거는 없었습니다"], size=46, accent=1)


# ───────────────────────────── 샷: 08 실질임금

def s_good_news(p):
    return stmt(p, ["그럼 좋은 소식일까요"], size=48)


def s_nominal(p):
    fig = newfig()
    kinetic(fig, 0.5, 0.775, "공개된 연봉 중앙값", p, 30, T["ink3"],
            weight="normal", ha="center")
    v = countup(185, p, 0.10, 0.72)
    fig.text(0.5, 0.525, f"${int(v)}k", fontsize=118, color=T["ink"],
             ha="center", va="center", fontweight="bold")
    a = fade(p, 0.16, 0.34)
    if a > 0.02:
        fig.text(0.5, 0.315, "2016년  $120k", fontsize=27, color=T["ink3"],
                 ha="center", alpha=a)
    kinetic(fig, 0.5, 0.155, "+54%", p, 52, T["ink"], ha="center", delay=0.66)
    return fig


def s_cpi(p):
    fig = newfig()
    kinetic(fig, 0.5, 0.775, "같은 기간 물가", p, 30, T["ink3"],
            weight="normal", ha="center")
    v = countup(40, p, 0.10, 0.72)
    fig.text(0.5, 0.505, f"+{int(v)}%", fontsize=124, color=T["s2"],
             ha="center", va="center", fontweight="bold")
    kinetic(fig, 0.5, 0.235, "미국 소비자물가지수", p, 24, T["ink3"],
            weight="normal", ha="center", delay=0.60)
    return fig


def s_subtract(p):
    """+54% 에서 물가를 뺀다."""
    fig = newfig()
    fig.text(0.5, 0.735, "연봉", fontsize=26, color=T["ink3"], ha="center")
    fig.text(0.5, 0.615, "+54%", fontsize=76, color=T["ink"], ha="center",
             va="center", fontweight="bold")
    a = fade(p, 0.14, 0.34)
    if a > 0.02:
        # U+2212 는 Apple SD Gothic Neo 에 없어 두부가 된다. 도형으로 그린다
        fig.patches.append(mpatches.Rectangle(
            (0.5 - 0.021, 0.4735), 0.042, 0.007, transform=fig.transFigure,
            facecolor=T["ink3"], alpha=a, zorder=6))
        fig.text(0.5, 0.395, "물가", fontsize=26, color=T["ink3"], ha="center",
                 alpha=a)
        fig.text(0.5, 0.285, "+40%", fontsize=76, color=T["s2"], ha="center",
                 va="center", fontweight="bold", alpha=a)
    ln = ease(min(1, max(0, (p - 0.52) / 0.24)))
    if ln > 0.01:
        fig.patches.append(mpatches.Rectangle(
            (0.5 - 0.16 * ln, 0.185), 0.32 * ln, 0.005,
            transform=fig.transFigure, facecolor=T["ink3"], zorder=6))
    return fig


def s_left(p):
    fig = newfig()
    kinetic(fig, 0.5, 0.735, "남는 것", p, 30, T["ink3"], weight="normal",
            ha="center")
    v = countup(12, p, 0.08, 0.62)
    fig.text(0.5, 0.475, f"+{int(v)}%", fontsize=138, color=T["s2"],
             ha="center", va="center", fontweight="bold")
    kinetic(fig, 0.5, 0.185, "10년 동안", p, 30, T["ink2"], weight="normal",
            ha="center", delay=0.60)
    return fig


# ───────────────────────────── 샷: 09 한계

def s_l_head(p):
    return stmt(p, ["믿기 전에", "알아야 할 것들"], size=46)


def _numbered(p, num, lines, accent=None, sub=None):
    fig = newfig()
    fig.text(0.085, 0.845, num, fontsize=90, color=T["grid"],
             fontweight="bold", va="top")
    for i, line in enumerate(lines):
        c = T["s2"] if accent == i else T["ink"]
        kinetic(fig, 0.085, 0.585 - i * 0.115, line, p, 40, c,
                delay=0.05 + i * 0.16)
    if sub:
        kinetic(fig, 0.085, 0.585 - len(lines) * 0.115 - 0.02, sub, p, 26,
                T["ink3"], weight="normal", delay=0.10 + len(lines) * 0.16)
    return fig


def s_l1a(p):
    return _numbered(p, "1", ["대조군이 완벽하지 않습니다"],
                     sub="미국 밖도 1.0% → 4.2%로 올랐다")


def s_l1b(p):
    return _numbered(p, "1", ["유럽에도", "비슷한 지침이 있습니다"])


def s_l1c(p):
    fig = newfig()
    kinetic(fig, 0.085, 0.855, "대조군도 함께 치료를 받으면", p, 36, T["ink2"],
            weight="normal")
    kinetic(fig, 0.085, 0.635, "차이는 줄어듭니다", p, 44, T["ink"], delay=0.20)
    kinetic(fig, 0.085, 0.395, "진짜 효과는", p, 40, T["ink"], delay=0.46)
    kinetic(fig, 0.085, 0.265, "제가 계산한 것보다 클 수 있습니다", p, 40,
            T["s2"], delay=0.60)
    return fig


def s_l2a(p):
    return _numbered(p, "2", ["해마다 연봉을 공개한", "회사가 다릅니다"])


def s_l2b(p):
    """같은 회사를 따라간 게 아니다."""
    fig = newfig()
    kinetic(fig, 0.5, 0.865, "같은 회사를 따라간 게 아닙니다", p, 36, T["ink"],
            ha="center")
    for i, yr in enumerate(["2016", "2021", "2026"]):
        a = fade(p, 0.16 + i * 0.18, 0.16 + i * 0.18 + 0.18)
        if a <= 0.02:
            continue
        x = 0.10 + i * 0.30
        fig.text(x + 0.13, 0.665, yr, fontsize=24, color=T["ink3"],
                 ha="center", alpha=a)
        for j in range(9):
            cx, cy = j % 3, j // 3
            fig.patches.append(mpatches.FancyBboxPatch(
                (x + 0.035 + cx * 0.065, 0.505 - cy * 0.100), 0.050, 0.072,
                boxstyle="round,pad=0,rounding_size=0.008",
                transform=fig.transFigure,
                facecolor=[T["s1"], T["s2"], T["s3"]][(i + j) % 3],
                alpha=0.72 * a, zorder=3))
    kinetic(fig, 0.5, 0.135, "표본이 해마다 갈린다", p, 26, T["ink3"],
            weight="normal", ha="center", delay=0.66)
    return fig


def s_l3a(p):
    return _numbered(p, "3", ["기준 연도를 바꾸면", "실질 상승률이 흔들립니다"])


def s_l3b(p):
    """+2% ~ +14% 범위."""
    fig = newfig()
    kinetic(fig, 0.5, 0.865, "기준 연도에 따라", p, 34, T["ink2"],
            weight="normal", ha="center")
    a = ease(min(1, max(0, (p - 0.12) / 0.36)))
    for i, (yr, val, c) in enumerate([("2015년 기준", "+2%", T["ink3"]),
                                      ("2018년 기준", "+12%", T["s2"]),
                                      ("2019년 기준", "+14%", T["ink3"])]):
        aa = fade(p, 0.12 + i * 0.15, 0.12 + i * 0.15 + 0.18)
        if aa <= 0.02:
            continue
        x = 0.11 + i * 0.293
        fig.text(x + 0.135, 0.615, val, fontsize=64, color=c, ha="center",
                 va="center", fontweight="bold", alpha=aa)
        fig.text(x + 0.135, 0.485, yr, fontsize=22, color=T["ink3"],
                 ha="center", alpha=aa)
    kinetic(fig, 0.5, 0.235, "그래서 완전히 제자리라고까지는", p, 32, T["ink2"],
            weight="normal", ha="center", delay=0.62)
    kinetic(fig, 0.5, 0.130, "말하지 않겠습니다", p, 38, T["ink"], ha="center",
            delay=0.74)
    return fig


# ───────────────────────────── 샷: 10 정리

def s_s_head(p):
    return stmt(p, ["정리하면"], size=48)


def _bullet(p, idx, lines, accent=None):
    fig = newfig()
    for i in range(3):
        on = i <= idx
        fig.patches.append(mpatches.Circle(
            (0.085 + i * 0.030, 0.865), 0.0075, transform=fig.transFigure,
            facecolor=T["s2"] if on else T["grid"], zorder=4))
    for i, line in enumerate(lines):
        c = T["s2"] if accent == i else T["ink"]
        kinetic(fig, 0.085, 0.560 - i * 0.120, line, p, 44, c,
                delay=0.05 + i * 0.18)
    return fig


def s_s1(p):
    return _bullet(p, 0, ["연봉 공개는", "법이 있는 곳에서만 늘었다"], accent=1)


def s_s2(p):
    return _bullet(p, 1, ["범위를 넓게 써서", "피하고 있지도 않았다"])


def s_s3(p):
    return _bullet(p, 2, ["그런데 공개된 연봉 자체는", "물가를 빼면 거의 제자리였다"],
                   accent=1)


def s_s_line(p):
    return stmt(p, ["투명해진 것과", "나아진 것은"], size=48, sub="다른 문제였습니다")


def s_s_repo(p):
    fig = newfig()
    kinetic(fig, 0.5, 0.610, "데이터와 코드는 전부 공개합니다", p, 34, T["ink2"],
            weight="normal", ha="center")
    kinetic(fig, 0.5, 0.455, "github.com/controlarm/hn-hiring-analysis", p, 32,
            T["s1"], ha="center", delay=0.22)
    kinetic(fig, 0.5, 0.290, "대조군", p, 40, T["ink"], ha="center", delay=0.46)
    return fig


DRAW = {k[2:]: v for k, v in list(globals().items())
        if k.startswith("s_") and callable(v)}


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
