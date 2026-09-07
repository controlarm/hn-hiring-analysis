"""
3편 3막용: 공개된 연봉이 오른 게 실제로 오른 것인가.

연봉 공개율이 오르면서 중앙값 밴드도 올랐다($110–150k -> $150–210k).
그런데 그 사이 물가도 올랐다. 물가를 빼고 나면 뭐가 남는지 본다.

CPI 는 FRED 의 공개 CSV 에서 받는다. API 키가 필요 없다.
  CPIAUCSL = 도시 소비자물가지수, 계절조정, 월별

주의: 표본이 해마다 바뀐다. 2015년에 연봉을 공개한 회사와
2026년에 공개한 회사는 다른 집단이다. 같은 회사를 추적한 게 아니다.
-> 영상 한계 절에 반드시 넣을 것.

usage: .venv/bin/python ep03_cpi.py
"""

import io
import urllib.request

import numpy as np
import pandas as pd

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
BASE = 2026          # 이 해의 달러로 환산한다


def cpi_by_year():
    with urllib.request.urlopen(FRED, timeout=30) as r:
        c = pd.read_csv(io.StringIO(r.read().decode()))
    c.columns = ["date", "cpi"]
    c["date"] = pd.to_datetime(c["date"])
    c = c[c["date"].dt.year >= 2010]
    return c.groupby(c["date"].dt.year)["cpi"].mean()


def main():
    cpi = cpi_by_year()
    df = pd.read_csv("data/ep03_salary.csv")
    df = df[df["has"] & df["lo"].notna()]
    df["mid"] = (df["lo"] + df["hi"]) / 2
    df["width"] = (df["hi"] - df["lo"]) / df["lo"] * 100

    print("=" * 76)
    print(f"공개된 연봉 — 명목 vs 실질 ({BASE}년 달러 기준)")
    print("=" * 76)
    print(f"{'연도':<7}{'n':>6}{'하한':>8}{'상한':>8}{'중앙':>8}"
          f"{'실질중앙':>10}{'밴드폭':>9}")

    rows = []
    for y in range(2015, 2027):
        s = df[df.year == y]
        if len(s) < 20:                      # 표본이 적으면 중앙값이 튄다
            print(f"{y:<7}{len(s):>6}   (표본 부족, 건너뜀)")
            continue
        lo, hi = s["lo"].median(), s["hi"].median()
        mid, w = s["mid"].median(), s["width"].median()
        real = mid * cpi[BASE] / cpi[y]
        rows.append((y, mid, real, w))
        print(f"{y:<7}{len(s):>6}{lo:>7.0f}k{hi:>7.0f}k{mid:>7.0f}k"
              f"{real:>9.0f}k{w:>8.0f}%")

    a, b = rows[0], rows[-1]
    print(f"\n{a[0]} -> {b[0]}")
    print(f"  명목 중앙값  {a[1]:.0f}k -> {b[1]:.0f}k   ({(b[1]/a[1]-1)*100:+.0f}%)")
    print(f"  실질 중앙값  {a[2]:.0f}k -> {b[2]:.0f}k   ({(b[2]/a[2]-1)*100:+.0f}%)")
    print(f"  물가 상승     {(cpi[b[0]]/cpi[a[0]]-1)*100:+.0f}%")
    print(f"  밴드 폭      {a[3]:.0f}% -> {b[3]:.0f}%")
    print("\n  -> 실질 변화가 0 근처면 '올랐다'는 착시다.")
    print("     밴드 폭이 좁아졌다면 '넓게 써서 법을 피한다'는 가설은 기각.")

    pd.DataFrame(rows, columns=["year", "nominal_k", f"real_{BASE}_k", "width_%"]) \
        .to_csv("data/ep03_real.csv", index=False)
    print("\n-> data/ep03_real.csv")


if __name__ == "__main__":
    main()
