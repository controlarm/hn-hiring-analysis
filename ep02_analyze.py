"""
2편 분석: 비자 언급 반등의 정체.

1편에서 "비자 언급 비율이 2018년 11.8% -> 2025년 3.5% -> 2026년 5.0% 로 반등"이라고
티저를 걸었다. 그런데 '비자를 언급했다'는 것과 '스폰서를 해준다'는 것은 다르다.
"no visa sponsorship" 도 언급이다.

그래서 언급 하나하나를 문맥 창(±90자)으로 잘라 부정어 유무로 분류한다.
  제공(offer)  : we sponsor / sponsorship available / H1B transfer ...
  거절(deny)   : no visa sponsorship / unable to sponsor / must be authorized ...

usage: .venv/bin/python ep02_analyze.py
"""

import re

import pandas as pd

pd.set_option("display.width", 200)

# ── 앵커를 두 단계로 나눈다 ──────────────────────────────────────
# 'sponsor' 만으로 잡으면 "We sponsor PyCon, DjangoCon" 같은 학회 후원이 섞인다.
# 그래서 이민 관련이 확실한 HARD 와, 문맥이 받쳐줘야만 인정하는 SOFT 로 분리.
HARD = re.compile(r"\b(visas?|h-?1b1?|green card|work permit|immigration|"
                  r"work authoriz\w+|work eligib\w+|right to work)\b", re.I)
SOFT = re.compile(r"\bsponsor\w*\b", re.I)
# SOFT 주변에 이게 있으면 비자 얘기가 아니다
NOT_IMMIGRATION = re.compile(r"\b(conference|meetup|event|pycon|djangocon|rustconf|"
                             r"podcast|open ?source|oss|community|hackathon|"
                             r"summit|booth|team|league|charity)\b", re.I)

# 문맥 창 안에 이게 있으면 '거절'
DENY = re.compile(
    r"\b(no|not|cannot|can't|cant|won't|wont|unable|without|don't|dont|does not|"
    r"do not|neither|unfortunately)\b[^.]{0,40}\b(visa|sponsor\w*|h-?1b)\b"
    r"|\b(visa|sponsor\w*|h-?1b)\b[^.]{0,25}\b(not|isn't|aren't|unavailable|"
    r"not available|not offered|not provided)\b"
    r"|\bmust (already )?(be |have )?(legally )?(authorized|eligible|permitted)\b"
    r"|\bauthoriz\w+ to work\b"
    r"|\bwork authorization (is )?required\b"
    r"|\bno (visa )?sponsorship\b", re.I)

# 문맥 창 안에 이게 있으면 '제공'
OFFER = re.compile(
    r"\b(we|will|can|do|happy to|able to|glad to|offer\w*|provide\w*|"
    r"available|assist\w*|help\w*|support\w*)\b[^.]{0,40}\bsponsor\w*"
    r"|\bsponsorship (is )?(available|offered|provided|possible)\b"
    r"|\bvisa (support|assistance|help|sponsorship available)\b"
    r"|\bh-?1b transfer\b|\bgreen card (sponsor\w*|process)\b"
    r"|\brelocation (and|&|\+) visa\b", re.I)

WIN = 90


def norm(text: str) -> str:
    """곱슬 아포스트로피를 ASCII 로. don’t / can’t 가 정규식에 안 걸리는 걸 막는다."""
    return text.replace("’", "'").replace("‘", "'")


def anchors(text: str):
    """비자 문맥이 확실한 위치만 돌려준다."""
    spans = [m.span() for m in HARD.finditer(text)]
    for m in SOFT.finditer(text):
        w = text[max(0, m.start() - 60): m.end() + 60]
        # 학회·오픈소스 후원 제외. 이민 토큰이 곁에 있어야 인정
        if NOT_IMMIGRATION.search(w):
            continue
        if HARD.search(w) or re.search(r"sponsor\w*\s+(you|candidates?|applicants?|"
                                       r"employees?|workers?|international)", w, re.I):
            spans.append(m.span())
    return sorted(set(spans))


def classify(text: str):
    """한 공고를 (제공, 거절) 플래그로. 둘 다일 수 있다(직무마다 다른 경우)."""
    text = norm(text)
    offer = deny = False
    for a, b in anchors(text):
        w = text[max(0, a - WIN): b + WIN]
        if DENY.search(w):      # 거절이 우선. "unable to sponsor" 가 제공으로 새지 않게
            deny = True
        elif OFFER.search(w):
            offer = True
    return offer, deny


def main():
    df = pd.read_parquet("data/posts.parquet")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    df = df[df["month"] <= df["month"].max() - 1]          # 진행 중인 달 제외
    df["year"] = df["month"].dt.year

    flags = df["text"].apply(classify)
    df["offer"] = [f[0] for f in flags]
    df["deny"] = [f[1] for f in flags]
    df["mention"] = df["text"].apply(lambda t: bool(anchors(norm(t))))

    n = df.groupby("year").size()
    tab = pd.DataFrame({
        "공고수": n,
        "언급%": (df.groupby("year")["mention"].mean() * 100).round(1),
        "제공%": (df.groupby("year")["offer"].mean() * 100).round(1),
        "거절%": (df.groupby("year")["deny"].mean() * 100).round(1),
    })
    # 언급한 공고 중 거절이 차지하는 비중 — 이게 핵심 지표
    tab["언급중_거절%"] = (tab["거절%"] / tab["언급%"] * 100).round(0)
    # 비율의 표준오차 (n 이 작은 해를 과신하지 않기 위해)
    p = tab["언급%"] / 100
    tab["언급%_±"] = (1.96 * (p * (1 - p) / tab["공고수"]) ** 0.5 * 100).round(1)

    print("=" * 84)
    print("비자 관련 언급의 분해  (HN 'Who is hiring?' 공고 전수)")
    print("=" * 84)
    print(tab.loc[2012:].to_string())

    print("\n[샘플] 2026년 '거절'로 분류된 문맥 8건")
    s = df[(df["year"] == 2026) & df["deny"]]
    for t in s["text"].head(8):
        t = norm(t); a, b = anchors(t)[0]
        print("  *", re.sub(r"\s+", " ", t[max(0, a - 70): b + 70]))

    print("\n[샘플] 2026년 '제공'으로 분류된 문맥 8건")
    s = df[(df["year"] == 2026) & df["offer"] & ~df["deny"]]
    for t in s["text"].head(8):
        t = norm(t); a, b = anchors(t)[0]
        print("  *", re.sub(r"\s+", " ", t[max(0, a - 70): b + 70]))

    tab.to_csv("data/ep02_visa.csv")

    # 근무형태별 교차표 — 렌더에서 매번 재계산하지 않도록 미리 저장
    low = df["text"].str.lower()
    df["onsite"] = low.str.contains(r"\bonsite\b|\bon-site\b", regex=True)
    df["remote"] = low.str.contains(r"\bremote\b", regex=True)
    r = df[df["year"] >= 2024]
    rows = []
    for name, m in [("onsite", r["onsite"]), ("remote", r["remote"] & ~r["onsite"])]:
        s2 = r[m]
        rows.append({"setup": name, "n": len(s2),
                     "offer": round(s2["offer"].mean() * 100, 2),
                     "deny": round(s2["deny"].mean() * 100, 2)})
    pd.DataFrame(rows).to_csv("data/ep02_worksetup.csv", index=False)
    print("\n-> data/ep02_visa.csv, data/ep02_worksetup.csv")


if __name__ == "__main__":
    main()
