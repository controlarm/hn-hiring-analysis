"""
2편 썸네일. 1편과 한 세트로 보이되 숫자는 겹치지 않게.

1편이 '-76%' 를 썼으므로 2편에서 '76%' 를 쓰면 채널 목록에서 혼동된다.
그래서 2편은 숫자 대신 '갈라지는 두 선' 을 주인공으로 쓴다.
채널 아이콘(교차하는 두 선)과도 시각적으로 이어진다.

usage: .venv/bin/python thumbnail_ep02.py  ->  out/thumb_ep02/*.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("out/thumb_ep02")
KR = "Apple SD Gothic Neo"
BG, INK, DIM = "#141413", "#ffffff", "#8f8e86"
BLUE, HOT = "#3987e5", "#eb6834"


def series():
    v = pd.read_csv("data/ep02_visa.csv", index_col=0)
    return v.loc[2015:, "제공%"], v.loc[2015:, "거절%"]


def canvas():
    mpl.rcParams["font.family"] = KR
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    ax = fig.add_axes([0.47, 0.17, 0.48, 0.66])
    ax.set_facecolor(BG)
    off, deny = series()
    ax.plot(off.index, off.values, color=BLUE, lw=11, solid_capstyle="round")
    ax.plot(deny.index, deny.values, color=HOT, lw=11, solid_capstyle="round")
    ax.plot([deny.index[-1]], [deny.values[-1]], "o", color=HOT, ms=26,
            mec=BG, mew=5, zorder=5)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    # 선이 뭘 뜻하는지 한 단어씩
    ax.text(off.index[-1] + 0.25, off.values[-1], "해준다", color=BLUE,
            fontsize=30, fontweight="bold", va="center")
    ax.text(deny.index[-1] + 0.25, deny.values[-1], "안 해준다", color=HOT,
            fontsize=30, fontweight="bold", va="center")
    ax.set_xlim(off.index[0], off.index[-1] + 4.2)
    return fig


def variant_a():
    fig = canvas()
    fig.text(0.055, 0.755, "미국 비자 스폰서", fontsize=42, color=DIM, va="top")
    fig.text(0.055, 0.635, "늘어난 건", fontsize=76, color=INK,
             va="top", fontweight="bold")
    fig.text(0.055, 0.475, "\"안 해준다\"", fontsize=76, color=HOT,
             va="top", fontweight="bold")
    fig.text(0.058, 0.185, "공고 92,730건을 세어봤습니다", fontsize=23, color=DIM)
    fig.savefig(OUT / "thumb_a.png", facecolor=BG)
    plt.close(fig)


def variant_b():
    fig = canvas()
    fig.text(0.055, 0.755, "\"요즘 비자가 막혔다\"", fontsize=40, color=DIM, va="top")
    fig.text(0.055, 0.635, "15년째", fontsize=76, color=INK,
             va="top", fontweight="bold")
    fig.text(0.055, 0.475, "그대로였다", fontsize=76, color=BLUE,
             va="top", fontweight="bold")
    fig.text(0.058, 0.185, "공고 92,730건을 세어봤습니다", fontsize=23, color=DIM)
    fig.savefig(OUT / "thumb_b.png", facecolor=BG)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    variant_a()
    variant_b()
    try:
        from PIL import Image
        for p in sorted(OUT.glob("thumb_?.png")):
            Image.open(p).resize((350, 197), Image.LANCZOS).save(
                OUT / f"{p.stem}_preview.png")
    except ImportError:
        pass
    for p in sorted(OUT.glob("*.png")):
        print(f"  {p}  {p.stat().st_size // 1024}KB")
