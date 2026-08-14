"""
썸네일 2안. 1280x720.

차트를 그대로 크롭하면 썸네일 크기에서 글씨가 안 읽힌다.
그래서 같은 데이터로 '선 하나 + 큰 글씨'만 새로 그린다.

usage: .venv/bin/python thumbnail.py  ->  out/thumb/*.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("out/thumb")
KR = "Apple SD Gothic Neo"

BG = "#141413"
INK = "#ffffff"
DIM = "#8f8e86"
HOT = "#eb6834"   # 라이트 슬롯2 — 어두운 배경에서 더 강하게 튄다


def series():
    s = pd.read_csv("data/keyword_share.csv", index_col=0)
    s.index = pd.PeriodIndex(s.index, freq="M")
    h = s.groupby([s.index.year, (s.index.month > 6).astype(int)])["Data scientist"].mean()
    h.index = range(len(h))
    return h[h.index >= 12]  # 2017년부터


def canvas():
    mpl.rcParams.update({"font.family": KR})
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    # 우측 55%에 선, 좌측에 글씨. 우하단은 재생시간 표시가 덮으므로 비운다
    ax = fig.add_axes([0.47, 0.20, 0.48, 0.62])
    ax.set_facecolor(BG)
    y = series()
    ax.plot(y.index, y.values, color=HOT, lw=11, solid_capstyle="round",
            solid_joinstyle="round")
    ax.plot([y.index[-1]], [y.values[-1]], "o", color=HOT, ms=30,
            mec=BG, mew=6, zorder=5)
    ax.set_ylim(0, y.max() * 1.15)
    ax.axis("off")
    return fig


def variant_a():
    fig = canvas()
    fig.text(0.055, 0.755, '"data scientist"', fontsize=47,
             color=INK, va="top", fontweight="bold")
    fig.text(0.055, 0.60, "-76%", fontsize=168, color=HOT,
             va="top", fontweight="bold")
    fig.text(0.058, 0.185, "채용공고 92,730건 전수 분석", fontsize=23, color=DIM)
    fig.savefig(OUT / "thumb_a.png", facecolor=BG)
    plt.close(fig)


def variant_b():
    fig = canvas()
    fig.text(0.055, 0.775, "데이터 사이언티스트", fontsize=43,
             color=INK, va="top")
    fig.text(0.055, 0.655, "어디로 갔나", fontsize=80, color=INK,
             va="top", fontweight="bold")
    fig.text(0.055, 0.44, "-76%", fontsize=96, color=HOT,
             va="top", fontweight="bold")
    fig.text(0.058, 0.185, "공고 92,730건을 세어봤습니다", fontsize=23, color=DIM)
    fig.savefig(OUT / "thumb_b.png", facecolor=BG)
    plt.close(fig)


def previews():
    """피드에서 보이는 실제 크기로 축소 저장 — 여기서 안 읽히면 실패한 썸네일."""
    from PIL import Image
    for p in sorted(OUT.glob("thumb_?.png")):
        Image.open(p).resize((350, 197), Image.LANCZOS).save(
            OUT / f"{p.stem}_preview.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    variant_a()
    variant_b()
    try:
        previews()
    except ImportError:
        print("(Pillow 없음 — 축소 미리보기 생략)")
    for p in sorted(OUT.glob("*.png")):
        print(p, f"{p.stat().st_size / 1024:.0f}KB")
