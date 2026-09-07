"""
3편 분석: 연봉 공개율 급등은 급여 투명성 법 때문인가.

미국 급여 투명성 법 시행
  콜로라도 2021.01 · 뉴욕시 2022.11 · 캘리포니아/워싱턴 2023.01 · 일리노이/미네소타 2025.01

관찰: HN 공고의 연봉 공개율이 2015년 0.9% -> 2026년 16.2% 로 올랐다.
그런데 이걸 법 효과라고 부르려면, **법이 적용되지 않는 공고는 안 올랐어야** 한다.
그래서 대조군을 만든다.

  처치군: 미국 지역만 언급한 공고   (법 적용)
  대조군: 비미국 지역만 언급한 공고 (법 미적용)

둘 다 언급했거나 지역을 못 찾은 공고는 **버린다.** 섞이면 대조군이 아니다.

usage: .venv/bin/python ep03_analyze.py
"""

import re

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)

# 약어(CA, NY)는 위험하다. 도시·주 이름으로 잡는다
US = re.compile(
    r"\b(usa|u\.s\.a?\.?|united states|san francisco|bay area|silicon valley|"
    r"new york|nyc|brooklyn|manhattan|seattle|austin|boston|chicago|denver|boulder|"
    r"los angeles|san diego|san jose|palo alto|mountain view|sunnyvale|oakland|"
    r"portland|atlanta|miami|dallas|houston|philadelphia|washington,? d\.?c\.?|"
    r"pittsburgh|minneapolis|salt lake|phoenix|raleigh|durham|nashville|detroit|"
    r"california|colorado|massachusetts|texas|florida|illinois|virginia|"
    r"remote \(us|us[- ]remote|remote[- ]us\b|us[- ]based|us[- ]only)\b", re.I)

NONUS = re.compile(
    r"\b(london|berlin|munich|hamburg|paris|amsterdam|rotterdam|zurich|zug|geneva|"
    r"dublin|barcelona|madrid|lisbon|porto|milan|rome|stockholm|copenhagen|oslo|"
    r"helsinki|warsaw|krakow|prague|budapest|bucharest|vienna|brussels|"
    r"toronto|vancouver|montreal|ottawa|waterloo|"
    r"sydney|melbourne|brisbane|auckland|wellington|"
    r"singapore|tokyo|osaka|seoul|hong kong|shanghai|beijing|shenzhen|taipei|"
    r"bangalore|bengaluru|mumbai|delhi|hyderabad|pune|chennai|"
    r"tel aviv|jerusalem|haifa|dubai|abu dhabi|"
    r"sao paulo|são paulo|buenos aires|mexico city|bogota|santiago|"
    r"lagos|nairobi|cape town|johannesburg|"
    r"united kingdom|\buk\b|england|scotland|ireland|germany|france|netherlands|"
    r"switzerland|spain|portugal|italy|sweden|norway|denmark|finland|poland|"
    r"czech|austria|belgium|canada|australia|new zealand|india|israel|japan|"
    r"korea|china|brazil|argentina|mexico|nigeria|kenya|south africa|"
    r"remote \(eu|remote eu|eu[- ]remote|emea|apac|europe)\b", re.I)

# "$120k - $180k", "$120,000-$180,000", "120-180k"
PAT = re.compile(r"\$\s?(\d{2,3})(?:,?\d{3})?\s?k?\s?[-–—]{1,2}\s?\$?\s?"
                 r"(\d{2,3})(?:,?\d{3})?\s?k", re.I)


def band(t):
    m = PAT.search(t)
    if not m:
        return None
    lo, hi = int(m.group(1)), int(m.group(2))
    if not (40 <= lo <= 600 and 40 <= hi <= 900 and hi >= lo):
        return None
    return lo, hi


def region(text):
    """공고 앞부분(제목 줄)에 지역이 몰려 있다. 뒤쪽 본문은 잡음이 많다."""
    head = text[:200]
    u, n = bool(US.search(head)), bool(NONUS.search(head))
    if u and not n:
        return "US"
    if n and not u:
        return "non-US"
    return "mixed/unknown"


def ci(k, n):
    if n == 0:
        return "—"
    p = k / n
    return f"{p*100:5.1f}% ±{1.96*np.sqrt(p*(1-p)/n)*100:.1f}"


def main():
    df = pd.read_parquet("data/posts.parquet")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    df = df[df["month"] <= df["month"].max() - 1]
    df["year"] = df["month"].dt.year
    df = df[df["year"] >= 2015]

    b = df["text"].apply(band)
    df["has"] = b.notna()
    df["lo"] = [x[0] if x else np.nan for x in b]
    df["hi"] = [x[1] if x else np.nan for x in b]
    df["region"] = df["text"].apply(region)

    print("=" * 78)
    print("지역 분류 결과")
    print("=" * 78)
    print(df["region"].value_counts().to_string())
    print(f"\n분석에 쓰는 것: US + non-US = "
          f"{(df.region != 'mixed/unknown').sum():,}건 "
          f"({(df.region != 'mixed/unknown').mean()*100:.0f}%)")

    print("\n" + "=" * 78)
    print("연봉 공개율 — 처치군(미국) vs 대조군(비미국)")
    print("=" * 78)
    print(f"{'연도':<6}{'미국':>18}{'n':>7}{'   ':<3}{'비미국':>18}{'n':>7}")
    for y in range(2015, 2027):
        s = df[df.year == y]
        us, no = s[s.region == "US"], s[s.region == "non-US"]
        print(f"{y:<6}{ci(us.has.sum(), len(us)):>18}{len(us):>7}   "
              f"{ci(no.has.sum(), len(no)):>18}{len(no):>7}")

    print("\n※ 법 시행: 콜로라도 2021.01 · NYC 2022.11 · 캘리포니아·워싱턴 2023.01")

    # 법 시행 전후 변화량 비교 (이중차분의 아주 단순한 형태)
    pre = df[df.year.between(2018, 2021)]
    post = df[df.year.between(2024, 2026)]
    print("\n=== 2018–2021 → 2024–2026 변화 ===")
    for r in ["US", "non-US"]:
        a = pre[pre.region == r]["has"].mean() * 100
        c = post[post.region == r]["has"].mean() * 100
        print(f"  {r:<8} {a:5.1f}% → {c:5.1f}%   ({c-a:+5.1f}%p)")
    dus = (post[post.region == "US"]["has"].mean() - pre[pre.region == "US"]["has"].mean()) * 100
    dno = (post[post.region == "non-US"]["has"].mean() - pre[pre.region == "non-US"]["has"].mean()) * 100
    print(f"\n  차이의 차이 (DiD): {dus - dno:+.1f}%p")
    print("  -> 양수이고 크면 법 효과 가설과 부합. 0 근처면 다른 요인이 공통으로 작용")

    df[["month", "year", "region", "has", "lo", "hi"]].to_csv(
        "data/ep03_salary.csv", index=False)
    print("\n-> data/ep03_salary.csv")


if __name__ == "__main__":
    main()
