"""
2편 장면 렌더러. render.py 의 공통 요소(팔레트·제목블록·축·이징)를 그대로 쓴다.

1편과 다른 점: 1번 장면이 정지 카드가 아니라 차트다.
피드에서 스치는 시청자에게 첫 프레임이 정지 화면이면 AI 슬롭으로 읽힌다.

usage: .venv/bin/python render_ep02.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from render import (LEFT, THEMES, axes, big_card, chrome, fade, label,
                    list_card, newfig, partial, quote_card, style, unit)

OUT = Path("out/frames_ep02")

SRC2 = ("Hacker News 'Ask HN: Who is hiring?' · 2011–2026 · 공고 92,730건 · "
        "문맥 분류로 제공/거절 구분 · 분석코드 공개")


def footer(fig):
    """chrome() 이 넣은 출처 줄을 2편용으로 교체. 내용으로 찾는다."""
    for t in fig.texts:
        if t.get_text().startswith("Hacker News"):
            t.set_text(SRC2)
            return


def data():
    v = pd.read_csv("data/ep02_visa.csv", index_col=0).rename(columns={
        "언급%": "mention", "제공%": "offer", "거절%": "deny",
        "언급중_거절%": "deny_share"})
    w = pd.read_csv("data/ep02_worksetup.csv")
    return v.loc[2012:], w


def visa_chart(t, p, head, sub, show=("deny",), focus=None, note=None):
    """제공/거절 연도별. show 에 있는 선만 그린다. focus 아닌 선은 흐리게."""
    v, _ = data()
    fig = newfig()
    chrome(fig, t, head, sub, t["s2"] if "deny" in show else t["s1"])
    ax = axes(fig)
    ax.set_xlim(v.index[0], v.index[-1])
    ax.set_ylim(0, 15 if "mention" in show else 3.3)
    ax.set_xticks(range(2012, 2027, 3))
    unit(ax, t, "해당 내용을 쓴 공고 비율 (%)")

    series = [("mention", "비자 언급", t["s2"]),
              ("offer", "스폰서 제공", t["s1"]), ("deny", "스폰서 거절", t["s2"])]
    for col, lab, c in series:
        if col not in show:
            continue
        dim = focus is not None and col != focus
        x, y = partial(list(v.index), list(v[col]), 1.0 if dim else p)
        ax.plot(x, y, color=c, lw=3, solid_capstyle="round", alpha=0.28 if dim else 1)
        label(ax, v.index[-1], v[col].iloc[-1], lab, c,
              (0.28 if dim else fade(p, 0.78)), size=17)

    if note:
        ax.annotate(note[0], (note[1], note[2]), xytext=(0, 22),
                    textcoords="offset points", ha="center", fontsize=18,
                    fontweight="bold", color=t["s2"], alpha=fade(p, 0.75))
    footer(fig)
    return fig


def share_chart(t, p):
    """언급 중 거절 비중. 하나의 선으로 7% -> 40% 를 보여준다."""
    v, _ = data()
    fig = newfig()
    chrome(fig, t, "비자 얘기가 나오면, 열에 넷은 거절이다",
           "비자를 언급한 공고 중 '스폰서 안 함'이 차지하는 비중", t["s2"])
    ax = axes(fig)
    ax.set_xlim(v.index[0], v.index[-1])
    ax.set_ylim(0, 48)
    ax.set_xticks(range(2012, 2027, 3))
    unit(ax, t, "언급 공고 중 거절 비중 (%)")
    x, y = partial(list(v.index), list(v["deny_share"]), p)
    ax.plot(x, y, color=t["s2"], lw=3.4, solid_capstyle="round")
    a = fade(p, 0.8)
    if a > 0.02:
        ax.plot([v.index[-1]], [v["deny_share"].iloc[-1]], "o", color=t["s2"],
                ms=14, mec=t["surface"], mew=3, zorder=5, alpha=a)
        ax.annotate("40%", (v.index[-1], v["deny_share"].iloc[-1]),
                    xytext=(-14, 16), textcoords="offset points", ha="right",
                    fontsize=22, fontweight="bold", color=t["s2"], alpha=a)
    footer(fig)
    return fig


def remote_bars(t, p):
    """원격 vs 온사이트 스폰서 제공률. 막대 두 개면 충분하다."""
    _, w = data()
    fig = newfig()
    chrome(fig, t, "원격 공고일수록 스폰서는 없었다",
           "2024–2026년 공고 기준. 원격은 '어디서든'이 아니라 '미국 안에서 원격'", t["s1"])
    ax = axes(fig, (LEFT, 0.20, 0.60, 0.46))
    ax.grid(False)
    ax.set_xlim(0, 2.9)
    ax.set_ylim(-0.75, 1.85)
    ax.set_xticks([])
    ax.set_yticks([])

    rows = [("온사이트 공고", float(w[w.setup == "onsite"]["offer"].iloc[0]), t["s1"]),
            ("원격 공고", float(w[w.setup == "remote"]["offer"].iloc[0]), t["s2"])]
    for i, (name, val, c) in enumerate(rows):
        y = 1 - i
        grow = min(1.0, max(0.0, (p - i * 0.18) / 0.55))
        ax.barh(y, val * grow, height=0.30, color=c, zorder=3)
        ax.text(0.02, y + 0.30, name, ha="left", va="bottom", fontsize=21,
                color=t["ink"], fontweight="bold")
        if grow > 0.85:
            ax.text(val * grow + 0.07, y, f"{val:.1f}%", va="center", fontsize=27,
                    fontweight="bold", color=c, alpha=fade(p, 0.55))
    ax.text(0.02, -0.62, "스폰서를 제공한다고 쓴 공고 비율", fontsize=15, color=t["ink3"])
    a = fade(p, 0.82)
    if a > 0.02:
        fig.text(0.80, 0.47, "4배", fontsize=88, fontweight="bold",
                 color=t["ink"], ha="center", va="center", alpha=a)
        fig.text(0.80, 0.375, "차이", fontsize=23, color=t["ink2"],
                 ha="center", alpha=a)
    footer(fig)
    return fig


QUOTE = ("\"We cannot sponsor visas and must hire in the US.\"\n"
         "\"No visa sponsorship.\"\n"
         "\"We don't sponsor visas at the moment.\"")

BUILDERS = {
    "01_hook": lambda t, p: visa_chart(
        t, p, "비자 얘기가 다시 늘었다",
        "미국 채용공고 중 비자·스폰서를 언급한 비율. 2025년 4.9% → 2026년 6.7%",
        show=("mention",)),
    "02_twist": lambda t, p: big_card(
        t, p, "늘어난 것 중", "76%", "\"우리는 스폰서를 안 합니다\"", t["s2"]),
    "03_data": lambda t, p: list_card(t, p, "어떻게 셌나", [
        "'비자 언급' 과 '스폰서 제공' 은 다르다",
        "\"no visa sponsorship\" 도 언급이다",
        "",
        "언급 하나하나를 앞뒤 90자까지 잘라",
        "제공 / 거절 로 분류했다"], t["s1"]),
    "04_decompose": lambda t, p: visa_chart(
        t, p, "반등한 1.4%p 중 1.1%p가 '거절'이었다",
        "거절 1.6% → 2.7%,  제공 1.0% → 1.3%", show=("offer", "deny")),
    "05_share": share_chart,
    "06_flat": lambda t, p: visa_chart(
        t, p, "그리고 '제공'은 15년째 움직이지 않았다",
        "2012년 0.8% → 2026년 1.3%. 원래부터 공고 100개 중 1개였다",
        show=("offer", "deny"), focus="offer"),
    "07_quote": lambda t, p: quote_card(
        t, p, QUOTE, "회사가 스폰서를 끊은 게 아니라, 안 한다고 쓰기 시작했다", t["s2"]),
    "08_remote": remote_bars,
    "09_limits": lambda t, p: list_card(t, p, "이 분석의 한계", [
        "1.  안 썼다고 안 해준다는 뜻은 아니다 — 센 건 '쓰인 말'이다",
        "2.  2026년은 7개월치(n=2,247). 거절 상승은 신뢰구간이 살짝 겹친다",
        "3.  방향은 2023년부터 일관되지만, 단정하기엔 이르다",
        "4.  여전히 실리콘밸리에 치우친 표본이다"], t["s2"]),
    "10_summary": lambda t, p: list_card(t, p, "정리", [
        "비자 언급은 늘었지만, 늘어난 건 거절이었다",
        "'제공'은 15년째 100개 중 1개에서 안 움직였다",
        "원격 공고일수록 스폰서는 더 없었다", "",
        "데이터 · 코드 전부 설명란에"], t["s1"]),
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
