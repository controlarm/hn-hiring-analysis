"""
스크립트 순서대로 번호 붙은 프레임 생성. Vrew에 순서대로 끌어다 놓으면 됨.

차트는 단계별로 쪼개서(선 1개 -> 2개 -> 강조) 컷 전환으로 애니메이션을 대신한다.
텍스트 카드도 같이 뽑아서 Vrew에서 자막 얹을 일을 줄인다.

usage: .venv/bin/python frames.py  ->  out/frames/{light,dark}/NN_*.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from charts import SRC, THEMES, endlabel, frame, style, titleblock

W, H, DPI = 16, 9, 120


def _fig(t):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    return fig


def _ax(fig):
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.075, right=0.845, top=0.79, bottom=0.115)
    return ax


# ------------------------------------------------------------------ 텍스트 카드
def card(t, out, head=None, lines=(), big=None, quote=None, sub=None):
    fig = _fig(t)
    y = 0.72

    if big:
        fig.text(0.5, 0.56, big, fontsize=110, fontweight="bold",
                 color=t["ink"], ha="center", va="center")
        if sub:
            fig.text(0.5, 0.37, sub, fontsize=24, color=t["ink2"], ha="center")
        if head:
            fig.text(0.5, 0.75, head, fontsize=28, color=t["ink2"], ha="center")
    elif quote:
        fig.text(0.5, 0.60, f"“{quote}”", fontsize=30, style="italic",
                 color=t["ink"], ha="center", va="center", wrap=True)
        fig.text(0.5, 0.40, sub or "", fontsize=20, color=t["ink2"], ha="center")
    else:
        if head:
            fig.text(0.08, 0.80, head, fontsize=40, fontweight="bold",
                     color=t["ink"], va="top")
            y = 0.63
        for ln in lines:
            fig.text(0.08, y, ln, fontsize=26, color=t["ink2"], va="top")
            y -= 0.105

    fig.savefig(out)
    plt.close(fig)


# ------------------------------------------------------------------ 차트 1 단계
def chart1_steps(t, d):
    r = d[["구인", "구직"]].rolling(12, min_periods=6).mean().dropna()
    peak_x, peak_y = r["구인"].idxmax(), r["구인"].max()
    cross = r[r["구직"] > r["구인"]].index[0]

    def base(step):
        fig = _fig(t)
        ax = _ax(fig)
        ax.plot(r.index, r["구인"], color=t["s1"], lw=2.6, solid_capstyle="round")
        endlabel(ax, r.index[-1], r["구인"].iloc[-1], "구인", t["s1"])
        ax.set_ylim(0, peak_y * 1.12)
        frame(ax, t, unit="월평균 게시글 수 (12개월 이동평균)", every=2)
        return fig, ax

    # A. 구인만
    fig, ax = base("a")
    titleblock(fig, t, "구인글: 15년 추이", "해커뉴스 'Who is hiring?' 월간 스레드")
    yield "03_ch1a_hire", fig

    # B. 피크 강조
    fig, ax = base("b")
    ax.plot([peak_x], [peak_y], "o", color=t["s1"], ms=11,
            mec=t["surface"], mew=2.5, zorder=5)
    ax.annotate("2018년 5월  972건", (peak_x, peak_y), xytext=(0, 22),
                textcoords="offset points", color=t["s1"], fontsize=19,
                fontweight="bold", ha="center")
    titleblock(fig, t, "피크는 2018년, 그리고 무너진다",
               "최근 12개월 평균 331건 — 피크 대비 66% 감소")
    yield "04_ch1b_peak", fig

    # C. 구직 등장
    fig, ax = base("c")
    ax.plot(r.index, r["구직"], color=t["s2"], lw=2.6, solid_capstyle="round")
    endlabel(ax, r.index[-1], r["구직"].iloc[-1], "구직", t["s2"])
    titleblock(fig, t, "대조군: 같은 계정이 같은 날 올리는 구직 스레드",
               "사이트가 시들었다면 이 선도 같이 내려가야 한다")
    yield "06_ch1c_control", fig

    # D. 교차 + 비율
    fig, ax = base("d")
    ax.plot(r.index, r["구직"], color=t["s2"], lw=2.6, solid_capstyle="round")
    endlabel(ax, r.index[-1], r["구직"].iloc[-1], "구직", t["s2"])
    ax.axvline(cross, color=t["ink2"], lw=1, ls=(0, (4, 4)), alpha=0.55)
    ax.annotate("2023년, 역전", (cross, peak_y), xytext=(12, -6),
                textcoords="offset points", color=t["ink2"], fontsize=16, va="top")
    titleblock(fig, t, "회사만 사라졌다",
               "구직글은 월 93건 → 470건. 5배가 됐다")
    yield "07_ch1d_cross", fig


# ------------------------------------------------------------------ 차트 2 단계
def chart2_steps(t, h):
    panels = [
        ("기존 ML 시대 용어", [("Machine learning", "machine learning"),
                          ("Data scientist", "data scientist")]),
        ("LLM 시대 용어", [("LLM", "LLM"), ("Agentic", "AI agent / agentic")]),
    ]

    def build(show_right):
        fig, axes = plt.subplots(1, 2, figsize=(W, H), dpi=DPI, sharey=True)
        fig.subplots_adjust(left=0.07, right=0.80, top=0.755, bottom=0.115, wspace=0.42)
        for i, (ax, (ptitle, series)) in enumerate(zip(axes, panels)):
            if i == 1 and not show_right:
                ax.set_title("", pad=16)
                ax.set_ylim(0, 16)
                frame(ax, t, every=3)
                ax.tick_params(labelleft=False)
                for s in ax.spines.values():
                    s.set_visible(False)
                ax.set_xticks([])
                ax.grid(False)
                continue
            for (col, label), c in zip(series, (t["s1"], t["s2"])):
                ax.plot(h.index, h[col], color=c, lw=2.6, solid_capstyle="round")
                endlabel(ax, h.index[-1], h[col].iloc[-1], label, c)
            ax.set_title(ptitle, fontsize=19, fontweight="bold",
                         color=t["ink"], loc="left", pad=16)
            ax.set_ylim(0, 16)
            frame(ax, t, every=3)
        return fig

    fig = build(False)
    titleblock(fig, t, "AI 붐인데, 'AI 직함'은 사라지고 있었다",
               "machine learning 11.6% → 2.9%,  data scientist 7.5% → 1.8%\n"
               "세로축 = 해당 단어를 언급한 공고 비율 (%)")
    yield "08_ch2a_old", fig

    fig = build(True)
    titleblock(fig, t, "수요가 사라진 게 아니라, 이름이 갈렸다",
               "LLM은 2022년까지 이 데이터에 한 번도 안 나온다. 지금은 14.7%\n"
               "세로축 = 해당 단어를 언급한 공고 비율 (%)")
    yield "09_ch2b_both", fig


# ------------------------------------------------------------------ 차트 3 단계
def chart3_steps(t, h):
    order = [("Onsite", t["s1"]), ("Remote", t["s2"]), ("Hybrid", t["s3"])]

    def build(n):
        fig = _fig(t)
        ax = _ax(fig)
        for col, c in order[:n]:
            ax.plot(h.index, h[col], color=c, lw=2.6, solid_capstyle="round")
            endlabel(ax, h.index[-1], h[col].iloc[-1], col, c)
        ax.set_ylim(0, 92)
        frame(ax, t, unit="해당 단어를 언급한 공고 비율 (%)", every=2)
        return fig, ax

    fig, ax = build(1)
    titleblock(fig, t, "사무실 출근은 74%에서 21%까지 떨어졌다가",
               "onsite를 언급한 공고 비율")
    yield "10_ch3a_onsite", fig

    fig, ax = build(2)
    pk = h["Remote"].idxmax()
    ax.annotate(f"원격 정점 {h['Remote'].max():.1f}%", (pk, h["Remote"].max()),
                xytext=(0, 16), textcoords="offset points",
                color=t["s2"], fontsize=17, fontweight="bold", ha="center")
    titleblock(fig, t, "원격근무는 2022년 초에 정점을 찍었다",
               "지금 54%. 사라지진 않았지만 정점은 지났다")
    yield "11_ch3b_remote", fig

    fig, ax = build(3)
    titleblock(fig, t, "그리고 2019년엔 없던 단어가 하나 들어왔다",
               "hybrid: 1.0% (2019) → 20% 근처. onsite는 34%로 반등")
    yield "12_ch3c_hybrid", fig


# ------------------------------------------------------------------ 티저 (비자)
def teaser(t, s):
    v = s["Visa"].groupby(s.index.year).mean()
    v = v[v.index >= 2015]
    fig = _fig(t)
    ax = _ax(fig)
    ax.plot(v.index, v.values, color=t["s2"], lw=2.8, solid_capstyle="round")
    ax.plot([v.index[-1]], [v.values[-1]], "o", color=t["s2"], ms=12,
            mec=t["surface"], mew=2.5, zorder=5)
    ax.annotate("다시 올라온다", (v.index[-1], v.values[-1]), xytext=(-14, 18),
                textcoords="offset points", color=t["s2"], fontsize=19,
                fontweight="bold", ha="right")
    ax.set_ylim(0, 14)
    ax.set_xticks(range(2015, 2027, 2))
    frame(ax, t, unit="비자를 언급한 공고 비율 (%)")
    titleblock(fig, t, "다음 편: 비자",
               "11.8% (2018) → 3.5% (2025), 그리고 올해 반등. 왜?")
    return fig


def main() -> None:
    d = pd.read_csv("data/hire_vs_seek.csv", index_col=0)
    d.index = pd.PeriodIndex(d.index, freq="M").to_timestamp()
    d = d[d.index >= "2014-01-01"]

    s = pd.read_csv("data/keyword_share.csv", index_col=0)
    s.index = pd.PeriodIndex(s.index, freq="M")
    h = s.groupby([s.index.year, (s.index.month > 6).astype(int)]).mean()
    h.index = pd.PeriodIndex([f"{y}-{'01' if p == 0 else '07'}" for y, p in h.index],
                             freq="M").to_timestamp()
    h = h[h.index >= "2017-01-01"]

    for name, t in THEMES.items():
        style(t)
        out = Path("out/frames") / name
        out.mkdir(parents=True, exist_ok=True)

        card(t, out / "01_hook.png", head="2018년 5월        →        2026년 7월",
             big="972  →  273", sub="한 달 동안 올라온 채용공고 수")

        card(t, out / "02_data.png", head="이 데이터가 뭐고, 뭐가 아닌지",
             lines=[
                 "해커뉴스 'Ask HN: Who is hiring?'  ·  2011.04 – 2026.07",
                 "182개월 전수  ·  공고 92,730건  ·  공개 API, 코드 공개",
                 "",
                 "전체 고용시장이 아니다.",
                 "실리콘밸리 스타트업 · 원격 채용에 심하게 치우친 표본이다.",
             ])

        for stem, fig in chart1_steps(t, d):
            fig.savefig(out / f"{stem}.png")
            plt.close(fig)

        card(t, out / "05_question.png",
             big="진짜 채용이 준 건가?", sub="아니면 해커뉴스가 시든 건가?")

        card(t, out / "07b_ratio.png", head="구인 / 구직 비율",
             big="9.4  →  0.7", sub="2018년        →        2026년")

        for stem, fig in chart2_steps(t, h):
            fig.savefig(out / f"{stem}.png")
            plt.close(fig)

        for stem, fig in chart3_steps(t, h):
            fig.savefig(out / f"{stem}.png")
            plt.close(fig)

        quote = ("We are all-in on Claude Code for scoping and shipping.\n"
                 "You get a seat on Day 1.")
        # 13 = 시청자가 읽는 시간, 13b = 나레이션이 해설하는 동안 같은 화면 유지
        card(t, out / "13_quote.png", quote=quote, sub="2026년 실제 채용공고 중에서")
        card(t, out / "13b_quote_after.png", quote=quote,
             sub="요구 스킬이 아니라, 복지 항목이었다")

        card(t, out / "14_limits.png", head="이 분석의 한계",
             lines=[
                 "1.  실리콘밸리 · 스타트업 · 원격 쪽으로 치우친 표본이다",
                 "2.  단어를 센 것이라 맥락을 못 본다 — 언급 ≠ 요구 스킬",
                 "3.  상승 중인 단어에 '피크 대비 %'를 쓰면 안 된다",
                 "4.  미국 데이터다. 한국 채용시장은 이 곡선을 따르지 않는다",
             ])

        card(t, out / "15_summary.png", head="정리",
             lines=[
                 "회사는 3분의 1로 줄었고, 지원자는 5배가 됐다",
                 "AI 수요는 늘었지만 그걸 부르는 이름이 바뀌었다",
                 "회사들은 이제 AI 툴을 복지처럼 판다",
                 "",
                 "데이터 · 코드 전부 설명란에",
             ])

        fig = teaser(t, s)
        fig.savefig(out / "16_teaser.png")
        plt.close(fig)

        print(f"{name}: {len(list(out.glob('*.png')))}장 -> {out}")


if __name__ == "__main__":
    main()
