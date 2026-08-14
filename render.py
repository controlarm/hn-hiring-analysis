"""
장면 렌더러. frames.py 를 대체한다.

모든 장면은 진행도 p (0~1) 를 받는다.
  p=1  -> 완성된 정지 화면 (썸네일/미리보기용)
  p<1  -> 데이터가 그려지는 중간 상태 (애니메이션용)

build_video.py 가 각 장면 앞 1.4초를 애니메이션으로 뽑고 나머지는 p=1 로 정지시킨다.
정지 구간에 줌/패닝은 넣지 않는다. 차트에 줌을 걸면 글씨가 뭉개진다.

usage: .venv/bin/python render.py          # 정지 PNG 18장 x 2테마
"""

import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUT = Path("out/frames")
KR = "Apple SD Gothic Neo"
W, H, DPI = 16, 9, 120

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#55544f", ink3="#8b8a83",
                  grid="#e7e6e2", s1="#2a78d6", s2="#eb6834", s3="#1baf7a"),
    "dark": dict(surface="#151514", ink="#f7f7f4", ink2="#b9b8b0", ink3="#77766f",
                 grid="#2b2a28", s1="#3987e5", s2="#e0663a", s3="#22b47d"),
}

SRC = "Hacker News 'Ask HN: Who is hiring?' · 2011.04–2026.07 · 공고 92,730건 · 분석코드 공개"

# 본문 좌측 기준선. 모든 장면이 같은 세로선에서 시작한다.
LEFT = 0.062


# ─────────────────────────────────────────────────────────── 공통
def style(t):
    mpl.rcParams.update({
        "font.family": KR, "font.size": 15,
        "figure.facecolor": t["surface"], "axes.facecolor": t["surface"],
        "savefig.facecolor": t["surface"],
        "text.color": t["ink"], "xtick.color": t["ink3"], "ytick.color": t["ink3"],
        "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": t["grid"], "grid.linewidth": 1,
        "xtick.bottom": True, "ytick.left": False,
    })


def ease(p):
    """가속 후 감속. 선이 기계적으로 안 그려지게."""
    return 0 if p <= 0 else 1 if p >= 1 else (1 - math.cos(math.pi * p)) / 2


def fade(p, start, end=None):
    """p 가 start~end 구간을 지나는 동안 0->1. 요소를 시차 등장시킬 때."""
    end = start + 0.18 if end is None else end
    return ease(min(1.0, max(0.0, (p - start) / (end - start))))


def partial(x, y, p):
    """선을 p 만큼만. 마지막 구간은 보간해서 끊김 없이 자란다."""
    n = len(x)
    if p >= 1:
        return x, y
    f = ease(p) * (n - 1)
    k = int(f)
    if k < 1:
        return x[:2], y[:2]
    frac = f - k
    xs, ys = list(x[:k + 1]), list(y[:k + 1])
    if k + 1 < n and frac > 0:
        x0, x1 = mpl.dates.date2num(x[k]) if hasattr(x[k], "year") else x[k], None
        if hasattr(x[k], "year"):
            x1 = mpl.dates.date2num(x[k + 1])
            xs.append(mpl.dates.num2date(x0 + (x1 - x0) * frac))
        else:
            xs.append(x[k] + (x[k + 1] - x[k]) * frac)
        ys.append(y[k] + (y[k + 1] - y[k]) * frac)
    return xs, ys


def chrome(fig, t, head, sub, accent, foot=True):
    """제목 블록. 색 막대 -> 헤드라인 -> 부제. 위치는 전 장면 동일."""
    fig.add_artist(plt.Line2D([LEFT, LEFT + 0.038], [0.945, 0.945],
                              color=accent, lw=4, solid_capstyle="butt"))
    fig.text(LEFT, 0.905, head, fontsize=34, fontweight="bold",
             color=t["ink"], va="top", linespacing=1.25)
    if sub:
        fig.text(LEFT, 0.828, sub, fontsize=17.5, color=t["ink2"],
                 va="top", linespacing=1.5)
    if foot:
        fig.text(LEFT, 0.042, SRC, fontsize=12, color=t["ink3"])


def axes(fig, rect=(LEFT, 0.115, 0.78, 0.60)):
    ax = fig.add_axes(rect)
    # 배경을 칠하지 않는다. 칠하면 나중에 그려지는 축이 앞 축의 직접라벨을 덮는다
    ax.patch.set_visible(False)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, labelsize=14)
    ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(4))
    return ax


def years(ax, every=2):
    ax.xaxis.set_major_locator(mdates.YearLocator(every))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def unit(ax, t, text):
    ax.text(0, 1.06, text, transform=ax.transAxes, fontsize=13.5,
            color=t["ink3"], ha="left", va="bottom")


def label(ax, x, y, text, color, alpha=1.0, size=18):
    if alpha <= 0.02:
        return
    ax.annotate(f"  {text}", (x, y), xytext=(9, 0), textcoords="offset points",
                color=color, fontsize=size, fontweight="bold", va="center",
                alpha=alpha, annotation_clip=False)


def newfig():
    return plt.figure(figsize=(W, H), dpi=DPI)


# ─────────────────────────────────────────────────────────── 데이터
_cache = {}


def data():
    if _cache:
        return _cache
    d = pd.read_csv("data/hire_vs_seek.csv", index_col=0)
    d.index = pd.PeriodIndex(d.index, freq="M").to_timestamp()
    _cache["vol"] = d[d.index >= "2014-01-01"]

    s = pd.read_csv("data/keyword_share.csv", index_col=0)
    s.index = pd.PeriodIndex(s.index, freq="M")
    h = s.groupby([s.index.year, (s.index.month > 6).astype(int)]).mean()
    h.index = pd.PeriodIndex([f"{y}-{'01' if q == 0 else '07'}" for y, q in h.index],
                             freq="M").to_timestamp()
    _cache["half"] = h[h.index >= "2017-01-01"]
    _cache["visa"] = s["Visa"].groupby(s.index.year).mean().loc[2015:]
    return _cache


# ─────────────────────────────────────────────────────────── 카드형 장면
def big_card(t, p, head, big, sub, accent):
    """숫자 하나로 때리는 화면. 숫자가 살짝 떠오르며 나타난다."""
    fig = newfig()
    a = fade(p, 0.0, 0.35)
    if head:
        fig.text(0.5, 0.70, head, fontsize=26, color=t["ink2"], ha="center",
                 alpha=fade(p, 0.0, 0.25))
    fig.text(0.5, 0.505 - 0.02 * (1 - a), big, fontsize=108, fontweight="bold",
             color=t["ink"], ha="center", va="center", alpha=a)
    if sub:
        fig.text(0.5, 0.33, sub, fontsize=23, color=t["ink2"], ha="center",
                 alpha=fade(p, 0.30, 0.60))
    fig.add_artist(plt.Line2D([0.5 - 0.03, 0.5 + 0.03], [0.245, 0.245],
                              color=accent, lw=4, alpha=fade(p, 0.45, 0.75)))
    return fig


def list_card(t, p, head, lines, accent):
    """항목이 한 줄씩 시차를 두고 올라온다."""
    fig = newfig()
    chrome(fig, t, head, None, accent, foot=False)
    y = 0.70
    for i, ln in enumerate(lines):
        a = fade(p, 0.12 * i, 0.12 * i + 0.30)
        if ln:
            fig.text(LEFT, y - 0.012 * (1 - a), ln, fontsize=25,
                     color=t["ink2"], va="top", alpha=a)
        y -= 0.098
    return fig


def quote_card(t, p, quote, sub, accent):
    fig = newfig()
    fig.add_artist(plt.Line2D([LEFT, LEFT], [0.42, 0.66], color=accent, lw=5,
                              alpha=fade(p, 0.0, 0.25)))
    fig.text(LEFT + 0.035, 0.545, quote, fontsize=31, color=t["ink"],
             va="center", linespacing=1.55, alpha=fade(p, 0.05, 0.45))
    fig.text(LEFT + 0.035, 0.375, sub, fontsize=19, color=t["ink3"],
             alpha=fade(p, 0.35, 0.70))
    return fig


# ─────────────────────────────────────────────────────────── 차트형 장면
def vol_chart(t, p, show_seek, cross, head, sub, new="hire"):
    """new = 이번 장면에서 새로 그려지는 선. 나머지는 이미 그려진 상태로 둔다.
    앞 장면에서 이미 본 선을 매번 다시 그리면 시청자가 진도를 잃는다."""
    d = data()["vol"]
    r = d[["구인", "구직"]].rolling(12, min_periods=6).mean().dropna()
    peak_y = r["구인"].max()

    fig = newfig()
    chrome(fig, t, head, sub, t["s1"])
    ax = axes(fig)
    ax.set_xlim(r.index[0], r.index[-1])
    ax.set_ylim(0, peak_y * 1.12)
    years(ax)
    unit(ax, t, "월평균 게시글 수 (12개월 이동평균)")

    ph = p if new == "hire" else 1.0
    x, y = partial(list(r.index), list(r["구인"]), ph)
    ax.plot(x, y, color=t["s1"], lw=3, solid_capstyle="round")
    label(ax, r.index[-1], r["구인"].iloc[-1], "구인", t["s1"],
          fade(p, 0.80) if new == "hire" else 1.0)

    if show_seek:
        ps = p if new == "seek" else 1.0
        x2, y2 = partial(list(r.index), list(r["구직"]), ps)
        ax.plot(x2, y2, color=t["s2"], lw=3, solid_capstyle="round")
        label(ax, r.index[-1], r["구직"].iloc[-1], "구직", t["s2"],
              fade(p, 0.80) if new == "seek" else 1.0)

    if cross:
        cx = r[r["구직"] > r["구인"]].index[0]
        a = fade(p, 0.10, 0.55)
        ax.axvline(cx, color=t["ink3"], lw=1, ls=(0, (4, 4)), alpha=0.6 * a)
        ax.annotate("2023년, 역전", (cx, peak_y * 1.04), xytext=(12, 0),
                    textcoords="offset points", color=t["ink2"], fontsize=16,
                    va="top", alpha=a)
    return fig, ax, r


def scene_03(t, p):
    return vol_chart(t, p, False, False, "구인글, 15년 추이",
                     "해커뉴스 'Who is hiring?' 월간 스레드")[0]


def scene_04(t, p):
    fig, ax, r = vol_chart(t, p, False, False, "피크는 2018년, 그리고 무너진다",
                           "최근 12개월 평균 331건 — 피크 대비 66% 감소", new=None)
    px, py = r["구인"].idxmax(), r["구인"].max()
    a = fade(p, 0.10, 0.55)
    if a > 0.02:
        ax.plot([px], [py], "o", color=t["s1"], ms=13, mec=t["surface"],
                mew=3, zorder=5, alpha=a)
        ax.annotate("2018년 5월  972건", (px, py), xytext=(0, 24),
                    textcoords="offset points", color=t["s1"], fontsize=20,
                    fontweight="bold", ha="center", alpha=a)
    return fig


def scene_06(t, p):
    return vol_chart(t, p, True, False, "회사만 사라졌다",
                     "구직글은 월 93건 → 470건. 다섯 배가 됐다", new="seek")[0]


def scene_07(t, p):
    return vol_chart(t, p, True, True, "두 선이 만나는 지점",
                     "2023년, 구직글이 구인글을 넘어선다", new=None)[0]


def terms(t, p, show_right, head, sub):
    h = data()["half"]
    panels = [("기존 ML 시대 용어", [("Machine learning", "machine learning"),
                                ("Data scientist", "data scientist")]),
              ("LLM 시대 용어", [("LLM", "LLM"), ("Agentic", "AI agent / agentic")])]

    fig = newfig()
    chrome(fig, t, head, sub + "\n세로축 = 해당 단어를 언급한 공고 비율 (%)", t["s1"])
    # 좌우 패널 폭을 줄여 직접라벨이 들어갈 자리를 만든다
    for i, (ptitle, series) in enumerate(panels):
        ax = axes(fig, (LEFT + i * 0.455, 0.115, 0.275, 0.545))
        ax.set_xlim(h.index[0], h.index[-1])
        ax.set_ylim(0, 16)
        years(ax, 3)
        if i == 1 and not show_right:
            ax.set_axis_off()
            continue
        ax.set_title(ptitle, fontsize=19.5, fontweight="bold", color=t["ink"],
                     loc="left", pad=16)
        pp = p if (i == 1 or not show_right) else 1.0
        for (col, lab), c in zip(series, (t["s1"], t["s2"])):
            x, y = partial(list(h.index), list(h[col]), pp)
            ax.plot(x, y, color=c, lw=3, solid_capstyle="round")
            label(ax, h.index[-1], h[col].iloc[-1], lab, c, fade(pp, 0.80), size=15)
    return fig


def scene_08(t, p):
    return terms(t, p, False, "AI 붐인데, 'AI 직함'은 사라지고 있었다",
                 "machine learning 11.6% → 2.9%,  data scientist 7.5% → 1.8%")


def scene_09(t, p):
    return terms(t, p, True, "수요가 사라진 게 아니라, 이름이 갈렸다",
                 "LLM은 2022년까지 이 데이터에 한 번도 안 나온다. 지금은 14.7%")


def work(t, p, n, head, sub, peak):
    h = data()["half"]
    order = [("Onsite", t["s1"]), ("Remote", t["s2"]), ("Hybrid", t["s3"])]
    fig = newfig()
    chrome(fig, t, head, sub, order[min(n - 1, 2)][1])
    ax = axes(fig)
    ax.set_xlim(h.index[0], h.index[-1])
    ax.set_ylim(0, 92)
    years(ax)
    unit(ax, t, "해당 단어를 언급한 공고 비율 (%)")
    for i, (col, c) in enumerate(order[:n]):
        pp = p if i == n - 1 else 1.0
        x, y = partial(list(h.index), list(h[col]), pp)
        ax.plot(x, y, color=c, lw=3, solid_capstyle="round")
        label(ax, h.index[-1], h[col].iloc[-1], col, c, fade(pp, 0.80))
    if peak:
        a = fade(p, 0.80)
        pk = h["Remote"].idxmax()
        ax.annotate(f"원격 정점 {h['Remote'].max():.1f}%", (pk, h["Remote"].max()),
                    xytext=(0, 20), textcoords="offset points", color=t["s2"],
                    fontsize=18, fontweight="bold", ha="center", alpha=a)
    return fig


def scene_16(t, p):
    v = data()["visa"]
    fig = newfig()
    chrome(fig, t, "다음 편: 비자",
           "11.8% (2018) → 3.5% (2025), 그리고 올해 반등. 왜?", t["s2"])
    ax = axes(fig)
    ax.set_xlim(v.index[0], v.index[-1])
    ax.set_ylim(0, 14)
    ax.set_xticks(range(2015, 2027, 2))
    unit(ax, t, "비자를 언급한 공고 비율 (%)")
    x, y = partial(list(v.index), list(v.values), p)
    ax.plot(x, y, color=t["s2"], lw=3.4, solid_capstyle="round")
    a = fade(p, 0.80)
    if a > 0.02:
        ax.plot([v.index[-1]], [v.values[-1]], "o", color=t["s2"], ms=14,
                mec=t["surface"], mew=3, zorder=5, alpha=a)
        ax.annotate("다시 올라온다", (v.index[-1], v.values[-1]), xytext=(-16, 20),
                    textcoords="offset points", color=t["s2"], fontsize=19,
                    fontweight="bold", ha="right", alpha=a)
    return fig


QUOTE = "We are all-in on Claude Code for scoping\nand shipping. You get a seat on Day 1."

BUILDERS = {
    "01_hook":         lambda t, p: big_card(t, p, "2018년 5월        →        2026년 7월",
                                             "972  →  273", "한 달 동안 올라온 채용공고 수", t["s1"]),
    "02_data":         lambda t, p: list_card(t, p, "이 데이터가 뭐고, 뭐가 아닌지", [
                           "해커뉴스 'Ask HN: Who is hiring?'  ·  2011.04 – 2026.07",
                           "182개월 전수  ·  공고 92,730건  ·  공개 API, 코드 공개", "",
                           "전체 고용시장이 아니다.",
                           "실리콘밸리 스타트업 · 원격 채용에 치우친 표본이다."], t["s1"]),
    "03_ch1a_hire":    scene_03,
    "04_ch1b_peak":    scene_04,
    "05_question":     lambda t, p: big_card(t, p, None, "진짜 채용이 준 건가?",
                                             "아니면 해커뉴스가 시든 건가?", t["s2"]),
    "06_ch1c_control": scene_06,
    "07_ch1d_cross":   scene_07,
    "07b_ratio":       lambda t, p: big_card(t, p, "구인 / 구직 비율", "9.4  →  0.7",
                                             "2018년        →        2026년", t["s2"]),
    "08_ch2a_old":     scene_08,
    "09_ch2b_both":    scene_09,
    "10_ch3a_onsite":  lambda t, p: work(t, p, 1, "사무실 출근은 74%에서 21%까지 떨어졌다가",
                                         "onsite를 언급한 공고 비율", False),
    "11_ch3b_remote":  lambda t, p: work(t, p, 2, "원격근무는 2022년 초에 정점을 찍었다",
                                         "지금 54%. 사라지진 않았지만 정점은 지났다", True),
    "12_ch3c_hybrid":  lambda t, p: work(t, p, 3, "그리고 2019년엔 없던 단어가 들어왔다",
                                         "hybrid: 1.0% (2019) → 20% 근처. onsite는 34%로 반등", False),
    "13_quote":        lambda t, p: quote_card(t, p, QUOTE, "2026년 실제 채용공고 중에서", t["s3"]),
    "13b_quote_after": lambda t, p: quote_card(t, p, QUOTE, "요구 스킬이 아니라, 복지 항목이었다", t["s3"]),
    "14_limits":       lambda t, p: list_card(t, p, "이 분석의 한계", [
                           "1.  실리콘밸리 · 스타트업 · 원격 쪽으로 치우친 표본이다",
                           "2.  단어를 센 것이라 맥락을 못 본다 — 언급 ≠ 요구 스킬",
                           "3.  상승 중인 단어에 '피크 대비 %'를 쓰면 안 된다",
                           "4.  미국 데이터다. 한국 시장은 이 곡선을 따르지 않는다"], t["s2"]),
    "15_summary":      lambda t, p: list_card(t, p, "정리", [
                           "회사는 3분의 1로 줄었고, 지원자는 5배가 됐다",
                           "AI 수요는 늘었지만 그걸 부르는 이름이 바뀌었다",
                           "회사들은 이제 AI 툴을 복지처럼 판다", "",
                           "데이터 · 코드 전부 설명란에"], t["s1"]),
    "16_teaser":       scene_16,
}


def render(stem, theme, p, dest):
    t = THEMES[theme]
    style(t)
    fig = BUILDERS[stem](t, p)
    fig.savefig(dest)
    plt.close(fig)


def main():
    for theme in THEMES:
        out = OUT / theme
        out.mkdir(parents=True, exist_ok=True)
        for stem in BUILDERS:
            render(stem, theme, 1.0, out / f"{stem}.png")
        print(f"{theme}: {len(BUILDERS)}장 -> {out}")


if __name__ == "__main__":
    main()
