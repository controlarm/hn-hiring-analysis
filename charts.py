"""
1편용 차트 3장 (라이트/다크 각각). 영상용 1920x1080.

usage: .venv/bin/python charts.py  ->  out/*.png
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

OUT = Path("out")
KR = "Apple SD Gothic Neo"

# dataviz 레퍼런스 팔레트 (validate_palette.js 통과: 인접쌍 CVD ΔE 9.1)
THEMES = {
    "light": dict(
        surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", grid="#e2e1dd",
        s1="#2a78d6", s2="#eb6834", s3="#1baf7a",
    ),
    "dark": dict(
        surface="#1a1a19", ink="#ffffff", ink2="#c3c2b7", grid="#33322f",
        s1="#3987e5", s2="#d95926", s3="#199e70",
    ),
}

SRC = "출처: Hacker News 'Ask HN: Who is hiring?' 2011.04–2026.07 · 공고 92,730건 · 분석코드 공개"


def style(t):
    mpl.rcParams.update({
        "font.family": KR, "font.size": 15,
        "figure.facecolor": t["surface"], "axes.facecolor": t["surface"],
        "savefig.facecolor": t["surface"],
        "text.color": t["ink"], "axes.labelcolor": t["ink2"],
        "xtick.color": t["ink2"], "ytick.color": t["ink2"],
        "axes.edgecolor": t["grid"], "axes.linewidth": 1,
        "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": t["grid"], "grid.linewidth": 1,
        "xtick.bottom": True, "ytick.left": False,
    })


def frame(ax, t, unit=None, every=None):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    if every:
        ax.xaxis.set_major_locator(mdates.YearLocator(every))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    if unit:
        # 회전 라벨은 눈금 숫자와 겹친다 -> 축 위에 가로로
        ax.text(0, 1.03, unit, transform=ax.transAxes,
                fontsize=13.5, color=t["ink2"], ha="left", va="bottom")


def endlabel(ax, x, y, text, color, dy=0):
    ax.annotate(f" {text}", (x, y), xytext=(8, dy), textcoords="offset points",
                color=color, fontsize=17, fontweight="bold", va="center")


def titleblock(fig, t, head, sub):
    fig.text(0.055, 0.945, head, fontsize=29, fontweight="bold", color=t["ink"], va="top")
    fig.text(0.055, 0.872, sub, fontsize=17, color=t["ink2"], va="top")
    fig.text(0.055, 0.035, SRC, fontsize=12.5, color=t["ink2"])


# ---------------------------------------------------------------- 1. 구인 vs 구직
def chart1(t, name):
    d = pd.read_csv("data/hire_vs_seek.csv", index_col=0)
    d.index = pd.PeriodIndex(d.index, freq="M").to_timestamp()
    d = d[d.index >= "2014-01-01"]
    r = d[["구인", "구직"]].rolling(12, min_periods=6).mean().dropna()

    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    fig.subplots_adjust(left=0.075, right=0.845, top=0.79, bottom=0.115)

    for col, c in (("구인", t["s1"]), ("구직", t["s2"])):
        ax.plot(r.index, r[col], color=c, lw=2.6, solid_capstyle="round")
        endlabel(ax, r.index[-1], r[col].iloc[-1], col, c)

    # 역전 지점
    cross = r[r["구직"] > r["구인"]].index[0]
    ax.axvline(cross, color=t["ink2"], lw=1, ls=(0, (4, 4)), alpha=0.55)
    ax.annotate("2023년, 역전", (cross, r["구인"].max() * 0.97),
                xytext=(12, 0), textcoords="offset points",
                color=t["ink2"], fontsize=15, va="top")

    ax.set_ylim(0, None)
    frame(ax, t, unit="월평균 게시글 수 (12개월 이동평균)", every=2)
    titleblock(fig, t,
               "채용공고는 3분의 1로 줄었고, 구직글은 5배가 됐다",
               "같은 스레드·같은 계정·같은 달. 구인 대비 구직 비율 9.4 (2018) → 0.7 (2026)")
    fig.savefig(OUT / f"1_volume_{name}.png")
    plt.close(fig)


# ------------------------------------------------------- 2. 사라지는 용어 vs 뜨는 용어
def chart2(t, name):
    s = pd.read_csv("data/keyword_share.csv", index_col=0)
    s.index = pd.PeriodIndex(s.index, freq="M")
    h = s.groupby([s.index.year, (s.index.month > 6).astype(int)]).mean()
    h.index = pd.PeriodIndex([f"{y}-{'01' if p == 0 else '07'}" for y, p in h.index],
                             freq="M").to_timestamp()
    h = h[h.index >= "2017-01-01"]

    panels = [
        ("기존 ML 시대 용어", [("Machine learning", "machine learning"),
                          ("Data scientist", "data scientist")]),
        ("LLM 시대 용어", [("LLM", "LLM"), ("Agentic", "AI agent / agentic")]),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=120, sharey=True)
    fig.subplots_adjust(left=0.07, right=0.80, top=0.755, bottom=0.115, wspace=0.42)

    for ax, (ptitle, series) in zip(axes, panels):
        for (col, label), c in zip(series, (t["s1"], t["s2"])):
            ax.plot(h.index, h[col], color=c, lw=2.6, solid_capstyle="round")
            endlabel(ax, h.index[-1], h[col].iloc[-1], label, c)
        ax.set_title(ptitle, fontsize=19, fontweight="bold", color=t["ink"],
                     loc="left", pad=16)
        ax.set_ylim(0, 16)
        frame(ax, t, every=3)

    titleblock(fig, t,
               "AI 붐인데 '머신러닝'과 '데이터 사이언티스트'는 공고에서 사라졌다",
               "2017년 대비 2026년: machine learning -75%, data scientist -76%. 그 자리를 LLM·agent가 채웠다\n"
               "세로축 = 해당 단어를 언급한 공고 비율 (%)")
    fig.savefig(OUT / f"2_terms_{name}.png")
    plt.close(fig)


# ---------------------------------------------------------------- 3. 근무 형태
def chart3(t, name):
    s = pd.read_csv("data/keyword_share.csv", index_col=0)
    s.index = pd.PeriodIndex(s.index, freq="M")
    h = s.groupby([s.index.year, (s.index.month > 6).astype(int)]).mean()
    h.index = pd.PeriodIndex([f"{y}-{'01' if p == 0 else '07'}" for y, p in h.index],
                             freq="M").to_timestamp()
    h = h[h.index >= "2017-01-01"]

    fig, ax = plt.subplots(figsize=(16, 9), dpi=120)
    fig.subplots_adjust(left=0.075, right=0.845, top=0.79, bottom=0.115)

    for col, c, dy in (("Remote", t["s2"], 0), ("Onsite", t["s1"], 0), ("Hybrid", t["s3"], 0)):
        ax.plot(h.index, h[col], color=c, lw=2.6, solid_capstyle="round")
        endlabel(ax, h.index[-1], h[col].iloc[-1], col, c, dy)

    pk = h["Remote"].idxmax()
    ax.annotate(f"원격 정점 {h['Remote'].max():.1f}%", (pk, h["Remote"].max()),
                xytext=(0, 16), textcoords="offset points",
                color=t["s2"], fontsize=15, fontweight="bold", ha="center")

    ax.set_ylim(0, 92)
    frame(ax, t, unit="해당 단어를 언급한 공고 비율 (%)", every=2)
    titleblock(fig, t,
               "원격근무는 2022년에 정점을 찍고 되돌아오는 중",
               "onsite는 21%까지 떨어졌다가 34%로 반등. hybrid는 사실상 2021년에 없던 단어")
    fig.savefig(OUT / f"3_worksetup_{name}.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        style(t)
        chart1(t, name)
        chart2(t, name)
        chart3(t, name)
        print(f"{name} 완료")
    print("->", sorted(p.name for p in OUT.glob("*.png")))
