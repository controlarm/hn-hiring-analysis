"""
채널 아이콘. 800x800 (유튜브 권장), 원형으로 잘려도 안 깨지게 여백을 둔다.

마크는 1편의 핵심 이미지 — 내려오는 선(구인)과 올라오는 선(구직)이 교차하는 그림.
채널명 '대조군'이 곧 방법론이고, 그 방법론의 그림이 곧 아이콘.
글자는 넣지 않는다. 아바타는 48px 로도 표시되므로 글자는 뭉갠다.

usage: .venv/bin/python avatar.py  ->  out/brand/*.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

OUT = Path("out/brand")
S = 8.0          # 800px @ dpi 100
DPI = 100

THEMES = {
    "dark":  dict(bg="#151514", a="#3987e5", b="#e0663a"),
    "light": dict(bg="#fcfcfb", a="#2a78d6", b="#eb6834"),
}


def mark(t, name, bg=True):
    fig = plt.figure(figsize=(S, S), dpi=DPI,
                     facecolor=t["bg"] if bg else "none")
    # 원형 크롭 안쪽에만 그린다 (반지름 0.5 원 안의 안전 영역)
    ax = fig.add_axes([0.26, 0.30, 0.48, 0.40])
    ax.set_facecolor("none")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    x = np.linspace(0, 1, 200)
    # 내려오는 선: 높게 시작해 완만히 꺾여 내려온다
    down = 0.93 - 0.86 / (1 + np.exp(-(x - 0.52) * 11))
    # 올라오는 선: 낮게 시작해 올라온다
    up = 0.07 + 0.62 / (1 + np.exp(-(x - 0.46) * 9))

    lw = 26
    ax.plot(x, down, color=t["a"], lw=lw, solid_capstyle="round", zorder=2)
    ax.plot(x, up, color=t["b"], lw=lw, solid_capstyle="round", zorder=1)

    # 교차점을 배경색 링으로 끊어 두 선이 겹치지 않고 앞뒤가 보이게
    i = int(np.argmin(np.abs(down - up)))
    ax.plot([x[i]], [down[i]], "o", ms=lw * 1.5,
            color=t["bg"] if bg else "#151514", zorder=1.5)
    ax.plot(x, down, color=t["a"], lw=lw, solid_capstyle="round", zorder=2)

    fig.savefig(OUT / f"{name}.png", transparent=not bg)
    plt.close(fig)


def banner(t, name):
    """채널 아트. 2560x1440, 안전영역(중앙 1546x423)에만 요소를 둔다."""
    mpl.rcParams["font.family"] = "Apple SD Gothic Neo"
    fig = plt.figure(figsize=(25.6, 14.4), dpi=100, facecolor=t["bg"])
    fig.text(0.5, 0.545, "대조군", fontsize=132, fontweight="bold",
             color="#f7f7f4" if t["bg"].startswith("#15") else "#0b0b0b",
             ha="center", va="center")
    fig.text(0.5, 0.468, "공개 데이터로 직접 확인합니다  ·  분석 코드 전부 공개",
             fontsize=40, color="#b9b8b0" if t["bg"].startswith("#15") else "#55544f",
             ha="center", va="top")
    fig.add_artist(plt.Line2D([0.47, 0.53], [0.615, 0.615], color=t["b"], lw=9))
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    mark(THEMES["dark"], "avatar_dark")
    mark(THEMES["light"], "avatar_light")
    mark(THEMES["dark"], "avatar_transparent", bg=False)
    banner(THEMES["dark"], "banner_dark")
    for p in sorted(OUT.glob("*.png")):
        print(f"  {p}  {p.stat().st_size // 1024}KB")
