"""
3편 썸네일. 1·2편과 한 세트로 보이되 시각적으로 겹치지 않게.

  1편 = 큰 숫자 하나 ('-76%')
  2편 = 갈라지는 두 선
  3편 = 두 숫자의 대비 (명목 vs 실질)

세 편을 채널 목록에서 나란히 봤을 때 서로 구분돼야 한다.
그래서 3편은 '선' 이 아니라 '두 숫자' 를 주인공으로 쓴다.

usage: .venv/bin/python thumbnail_ep03.py  ->  out/thumb_ep03/*.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("out/thumb_ep03")
KR = "Apple SD Gothic Neo"
BG, INK, DIM = "#141413", "#ffffff", "#8f8e86"
BLUE, HOT = "#3987e5", "#eb6834"


def real():
    r = pd.read_csv("data/ep03_real.csv")
    return r[r.year >= 2016]


def rates():
    d = pd.read_csv("data/ep03_salary.csv")
    us = d[d.region == "US"].groupby("year")["has"].mean() * 100
    no = d[d.region == "non-US"].groupby("year")["has"].mean() * 100
    return us, no


def canvas():
    mpl.rcParams["font.family"] = KR
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor=BG)
    return fig


def chart(fig, rect=(0.50, 0.17, 0.45, 0.66)):
    ax = fig.add_axes(rect)
    ax.set_facecolor(BG)
    ax.axis("off")
    return ax


def variant_a():
    """명목 vs 실질. 두 숫자의 대비가 주인공."""
    fig = canvas()
    ax = chart(fig)
    r = real()
    ax.plot(r.year, r["nominal_k"], color=BLUE, lw=11, solid_capstyle="round")
    ax.plot(r.year, r["real_2026_k"], color=HOT, lw=11, solid_capstyle="round")
    ax.set_ylim(105, 200)
    ax.set_xlim(2016, 2026.6)

    fig.text(0.055, 0.855, "연봉을 공개하는 공고가 늘었다", fontsize=33,
             color=DIM, va="top")
    fig.text(0.055, 0.715, "그런데 연봉은", fontsize=68, color=INK,
             va="top", fontweight="bold")
    fig.text(0.055, 0.545, "물가만큼만", fontsize=68, color=HOT,
             va="top", fontweight="bold")
    fig.text(0.055, 0.375, "올랐다", fontsize=68, color=HOT,
             va="top", fontweight="bold")
    # 80,854건은 미국만이 아니라 지역 분류 대상 전체다. 캡션에서 미국이라고 쓰면 틀린다
    fig.text(0.058, 0.115, "채용공고 80,854건을 세어봤습니다", fontsize=22, color=DIM)
    fig.savefig(OUT / "thumb_a.png", facecolor=BG)
    plt.close(fig)


def variant_b():
    """법 효과. 2023년에 갈라지는 처치군/대조군."""
    fig = canvas()
    ax = chart(fig)
    us, no = rates()
    ax.plot(us.index, us.values, color=HOT, lw=11, solid_capstyle="round")
    ax.plot(no.index, no.values, color=BLUE, lw=11, solid_capstyle="round")
    ax.axvline(2023, color=DIM, lw=3, ls=(0, (3, 3)))
    ax.set_ylim(0, 27)
    ax.set_xlim(2015, 2026.2)
    # 라벨은 선 끝 '위' 에 둔다. 오른쪽에 두면 선과 겹치고 가장자리에서 잘린다
    ax.text(2026, us.iloc[-1] + 1.2, "미국", color=HOT, fontsize=27,
            fontweight="bold", va="bottom", ha="right")
    ax.text(2026, no.iloc[-1] + 1.2, "미국 밖", color=BLUE, fontsize=27,
            fontweight="bold", va="bottom", ha="right")

    # 0.94% -> 16.20% = 17.2배. 올려 쓰지 말 것
    fig.text(0.055, 0.815, "연봉 공개가 17배 늘었다", fontsize=34,
             color=DIM, va="top")
    fig.text(0.055, 0.660, "법이 있는", fontsize=76, color=INK,
             va="top", fontweight="bold")
    fig.text(0.055, 0.480, "곳에서만", fontsize=76, color=HOT,
             va="top", fontweight="bold")
    fig.text(0.058, 0.185, "대조군을 만들어 확인했습니다", fontsize=23, color=DIM)
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
