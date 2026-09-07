"""
3편 장면 렌더러. render.py 의 공통 요소를 그대로 쓴다.

2편과 같은 훅 구조를 유지한다 — 1번 장면이 정지 카드가 아니라 움직이는 차트.
EXP-01 이 무효로 끝나 훅 가설이 아직 검증되지 않았으므로, 여기서 또 바꾸지 않는다.
이번 편에서 바꾸는 변수는 카테고리 하나뿐이다(EXP-02).

6번 장면(경계 분석)이 이 채널의 정체성이다. 버린 데이터가 결론을 바꾸는지
눈으로 보여주는 장면이라, 다른 장면보다 여유 있게 배치한다.

usage: .venv/bin/python render_ep03.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from render import (LEFT, THEMES, axes, big_card, chrome, fade, label,
                    list_card, newfig, partial, style, unit)

OUT = Path("out/frames_ep03")

SRC3 = ("Hacker News 'Ask HN: Who is hiring?' · 2015–2026 · 공고 80,854건 · "
        "지역·연봉 정규식 추출 · CPI: FRED · 분석코드 공개")

PRE = (2018, 2021)      # 법 시행 전
POST = (2024, 2026)     # 법 시행 후


def footer(fig):
    """chrome() 이 넣은 출처 줄을 3편용으로 교체. 내용으로 찾는다."""
    for t in fig.texts:
        if t.get_text().startswith("Hacker News"):
            t.set_text(SRC3)
            return


def salary():
    return pd.read_csv("data/ep03_salary.csv")


def rates():
    """연도별 공개율(%). 전체 / 처치군 / 대조군."""
    d = salary()
    g = d.groupby("year")["has"].mean() * 100
    us = d[d.region == "US"].groupby("year")["has"].mean() * 100
    no = d[d.region == "non-US"].groupby("year")["has"].mean() * 100
    return g, us, no


def did_bounds():
    """관측 DiD 와, 버린 공고를 한쪽으로 몰아넣은 두 극단."""
    d = salary()
    pre, post = d[d.year.between(*PRE)], d[d.year.between(*POST)]

    def delta(a, b, regions):
        return (b[b.region.isin(regions)]["has"].mean()
                - a[a.region.isin(regions)]["has"].mean()) * 100

    du, dn = delta(pre, post, ["US"]), delta(pre, post, ["non-US"])
    lo = du - delta(pre, post, ["non-US", "mixed/unknown"])
    hi = delta(pre, post, ["US", "mixed/unknown"]) - dn
    return du - dn, lo, hi


# ─────────────────────────── 장면 ───────────────────────────

def disclose(t, p, head, sub, show=("all",), focus=None, mark=None):
    """공개율 시계열. show 에 있는 선만 그린다."""
    g, us, no = rates()
    fig = newfig()
    chrome(fig, t, head, sub, t["s2"] if "us" in show else t["s1"])
    ax = axes(fig)
    ax.set_xlim(2015, 2026)
    ax.set_ylim(0, 25 if "us" in show else 18)
    ax.set_xticks(range(2015, 2027, 2))
    unit(ax, t, "연봉을 적은 공고 비율 (%)")

    for key, series, lab, c in [("all", g, "전체 공고", t["s1"]),
                                ("us", us, "미국 (법 적용)", t["s2"]),
                                ("no", no, "미국 밖 (법 없음)", t["s3"])]:
        if key not in show:
            continue
        dim = focus is not None and key != focus
        x, y = partial(list(series.index), list(series.values),
                       1.0 if dim else p)
        ax.plot(x, y, color=c, lw=3, solid_capstyle="round",
                alpha=0.28 if dim else 1)
        label(ax, series.index[-1], series.iloc[-1], lab, c,
              (0.28 if dim else fade(p, 0.78)), size=17)

    if mark:
        a = fade(p, 0.6)
        ax.axvline(mark, color=t["ink3"], lw=1.4, ls=(0, (4, 4)), alpha=a * 0.7)
        ax.annotate("캘리포니아·워싱턴\n급여 공개법 시행", (mark, 23.4),
                    xytext=(-8, 0), textcoords="offset points", ha="right",
                    va="top", fontsize=15, color=t["ink2"], alpha=a)
    footer(fig)
    return fig


def bounds_bars(t, p):
    """경계 분석. 버린 것을 어느 쪽에 몰아도 결론이 안 바뀐다는 걸 눈으로."""
    obs, lo, hi = did_bounds()
    fig = newfig()
    chrome(fig, t, "버린 데이터를 어느 쪽에 몰아도 결론은 같았다",
           "지역을 못 찾아 제외한 공고 31%를 극단적으로 가정했을 때의 차이의 차이",
           t["s1"])
    ax = axes(fig, (LEFT, 0.20, 0.62, 0.46))
    ax.grid(False)
    ax.set_xlim(0, 14.5)
    ax.set_ylim(-0.72, 2.45)
    ax.set_xticks([])
    ax.set_yticks([])

    rows = [("실제 분류", obs, t["s2"]),
            ("버린 것이 전부 미국이었다면", hi, t["s1"]),
            ("버린 것이 전부 미국 밖이었다면", lo, t["s1"])]
    for i, (name, val, c) in enumerate(rows):
        y = 2 - i
        grow = min(1.0, max(0.0, (p - i * 0.16) / 0.55))
        ax.barh(y, val * grow, height=0.30, color=c, zorder=3)
        ax.text(0.05, y + 0.30, name, ha="left", va="bottom", fontsize=19,
                color=t["ink"], fontweight="bold")
        if grow > 0.85:
            ax.text(val * grow + 0.25, y, f"+{val:.1f}%p", va="center",
                    fontsize=25, fontweight="bold", color=c,
                    alpha=fade(p, 0.55))
    ax.text(0.05, -0.60, "미국이 미국 밖보다 더 오른 정도 (차이의 차이)",
            fontsize=15, color=t["ink3"])
    footer(fig)
    return fig


def width_chart(t, p):
    """밴드 폭. 회피 가설을 기각하는 장면."""
    r = pd.read_csv("data/ep03_real.csv")
    r = r[r.year >= 2016]                 # 2015는 n=55라 폭이 튄다. 쓰지 않는다
    fig = newfig()
    chrome(fig, t, "범위를 넓게 써서 피하고 있지도 않았다",
           "공개된 연봉의 상한이 하한보다 얼마나 높은가. 넓을수록 정보가 적다", t["s1"])
    ax = axes(fig)
    ax.set_xlim(2016, 2026)
    ax.set_ylim(0, 60)
    ax.set_xticks(range(2016, 2027, 2))
    unit(ax, t, "연봉 범위의 폭 (%)")
    x, y = partial(list(r.year), list(r["width_%"]), p)
    ax.plot(x, y, color=t["s1"], lw=3, solid_capstyle="round")
    label(ax, r.year.iloc[-1], r["width_%"].iloc[-1], "밴드 폭", t["s1"],
          fade(p, 0.78), size=17)
    footer(fig)
    return fig


def real_chart(t, p):
    """명목 vs 실질. 이번 편의 반전."""
    r = pd.read_csv("data/ep03_real.csv")
    r = r[r.year >= 2016]
    fig = newfig()
    chrome(fig, t, "그런데 그 연봉은 물가만큼만 올랐다",
           "공개된 연봉 중앙값. 실질은 2026년 물가 기준으로 환산", t["s2"])
    ax = axes(fig)
    ax.set_xlim(2016, 2026)
    ax.set_ylim(100, 210)
    ax.set_xticks(range(2016, 2027, 2))
    unit(ax, t, "연봉 중앙값 (천 달러)")
    # 두 선은 2026년에 만난다. 그건 발견이 아니라 기준연도가 2026이라서 그렇다.
    # 오른쪽에 직접라벨을 달면 겹치고 오해도 부르므로, 갈라지는 왼쪽 끝에 단다.
    for col, lab, c, dy in [("nominal_k", "명목", t["s1"], -13),
                            ("real_2026_k", "실질 (물가 반영)", t["s2"], 13)]:
        x, y = partial(list(r.year), list(r[col]), p)
        ax.plot(x, y, color=c, lw=3, solid_capstyle="round")
        a = fade(p, 0.35)
        if a > 0.02:
            ax.annotate(lab, (r.year.iloc[0], r[col].iloc[0]), xytext=(10, dy),
                        textcoords="offset points", color=c, fontsize=17,
                        fontweight="bold", va="center", alpha=a)
    a = fade(p, 0.75)
    if a > 0.02:
        ax.annotate("두 선이 만나는 건\n2026년 물가를 기준으로 환산했기 때문",
                    (2026, 185), xytext=(-14, 40), textcoords="offset points",
                    ha="right", va="bottom", fontsize=14, color=t["ink3"], alpha=a)
    footer(fig)
    return fig


BUILDERS = {
    "01_hook": lambda t, p: disclose(
        t, p, "미국 채용공고가 연봉을 쓰기 시작했다",
        "연봉 범위를 적은 공고 비율. 2015년 0.9% → 2026년 16.2%"),
    "02_twist": lambda t, p: big_card(
        t, p, "그런데 물가를 빼면", "+12%", "명목으로는 절반 넘게 올랐다", t["s2"]),
    "03_data": lambda t, p: list_card(t, p, "어떻게 셌나", [
        "공고에서 '$120k – $180k' 같은 범위를 정규식으로 뽑았다",
        "지역이 미국만 적힌 공고 / 미국 밖만 적힌 공고로 나눴다",
        "",
        "둘 다 적혔거나 못 찾은 공고는 버렸다 — 섞이면 대조군이 아니다"], t["s1"]),
    "04_control": lambda t, p: disclose(
        t, p, "법이 적용되는 곳만 따로 봤다",
        "미국 지역만 적힌 공고. 급여 공개법의 적용 대상", show=("us",)),
    "05_jump": lambda t, p: disclose(
        t, p, "2023년, 미국만 두 배로 뛰었다",
        "미국 4.5% → 10.0%.  같은 해 미국 밖은 1.4% → 0.9%로 오히려 내려갔다",
        show=("us", "no"), mark=2023),
    "06_robust": bounds_bars,
    "07_avoid": width_chart,
    "08_real": real_chart,
    "09_limits": lambda t, p: list_card(t, p, "이 분석의 한계", [
        "1.  대조군도 조금 올랐다 — 유럽에도 비슷한 지침이 있다",
        "     대조군이 오염되면 효과는 과소추정된다. 실제는 더 클 수 있다",
        "2.  해마다 연봉을 공개한 회사가 다르다. 같은 회사를 추적한 게 아니다",
        "3.  기준 연도를 바꾸면 실질 상승률이 +2~14%로 흔들린다",
        "4.  지역은 공고 앞 200자로 판정했다. 31%는 판정 불가로 제외"], t["s2"]),
    "10_summary": lambda t, p: list_card(t, p, "정리", [
        "연봉 공개는 법이 있는 곳에서만 늘었다",
        "범위를 넓게 써서 피하고 있지도 않았다",
        "그런데 공개된 연봉 자체는 물가를 빼면 거의 제자리였다", "",
        "투명해진 것과 나아진 것은 다른 문제였다"], t["s1"]),
}


def render(stem, theme, p, dest):
    t = THEMES[theme]
    style(t)
    fig = BUILDERS[stem](t, p)
    fig.savefig(dest)
    plt.close(fig)


def main():
    obs, lo, hi = did_bounds()
    print(f"DiD 관측 {obs:+.1f}%p · 경계 {lo:+.1f} ~ {hi:+.1f}%p")
    for theme in THEMES:
        out = OUT / theme
        out.mkdir(parents=True, exist_ok=True)
        for stem in BUILDERS:
            render(stem, theme, 1.0, out / f"{stem}.png")
        print(f"{theme}: {len(BUILDERS)}장 -> {out}")


if __name__ == "__main__":
    main()
