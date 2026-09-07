"""
3편 견실성 점검: 지역을 못 찾아 버린 공고가 결과를 왜곡하는가.

ep03_analyze.py 는 지역이 mixed/unknown 인 공고 31% 를 버린다.
버리는 건 공짜가 아니다. 버린 쪽의 성격이 남긴 쪽과 다르면 결론이 흔들린다.

점검 셋:
  1. 버린 공고의 공개율이 남긴 것과 비슷한가 (다르면 선택편향 의심)
  2. mixed/unknown 비율이 연도별로 변했는가 (변했다면 시계열이 오염된다)
  3. 최악의 경우를 가정해도 DiD 가 살아남는가 (경계 분석)

usage: .venv/bin/python ep03_bias.py
"""

import numpy as np
import pandas as pd

from ep03_analyze import band, region


def ci(k, n):
    if n == 0:
        return "—"
    p = k / n
    return f"{p*100:5.1f}% ±{1.96*np.sqrt(p*(1-p)/n)*100:.1f}"


def load():
    df = pd.read_parquet("data/posts.parquet")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")
    df = df[df["month"] <= df["month"].max() - 1]
    df["year"] = df["month"].dt.year
    df = df[df["year"] >= 2015].copy()
    df["has"] = df["text"].apply(band).notna()
    df["region"] = df["text"].apply(region)
    return df


def rate(d):
    return d["has"].mean() * 100 if len(d) else np.nan


def main():
    df = load()
    pre = df[df.year.between(2018, 2021)]
    post = df[df.year.between(2024, 2026)]

    print("=" * 74)
    print("1. 버린 공고는 남긴 공고와 얼마나 다른가")
    print("=" * 74)
    for r in ["US", "non-US", "mixed/unknown"]:
        s = df[df.region == r]
        print(f"  {r:<16}{ci(s.has.sum(), len(s)):>16}   n={len(s):,}")
    print("\n  -> mixed 가 US 와 non-US 사이에 있으면 자연스럽다.")
    print("     (지역을 못 찾은 공고에는 양쪽이 섞여 있으므로)")

    print("\n" + "=" * 74)
    print("2. 버리는 비율이 연도별로 변했는가")
    print("=" * 74)
    print(f"{'연도':<8}{'mixed/unknown 비율':>20}{'전체 n':>10}")
    for y in range(2015, 2027):
        s = df[df.year == y]
        print(f"{y:<8}{(s.region == 'mixed/unknown').mean()*100:>19.1f}%{len(s):>10,}")
    print("\n  -> 이 비율이 크게 흔들리면, 남은 표본의 성격이 해마다 달라진다.")

    print("\n" + "=" * 74)
    print("3. 경계 분석 — 최악의 가정에서도 DiD 가 살아남는가")
    print("=" * 74)
    du = rate(post[post.region == "US"]) - rate(pre[pre.region == "US"])
    dn = rate(post[post.region == "non-US"]) - rate(pre[pre.region == "non-US"])
    print(f"  관측 DiD: {du - dn:+.1f}%p   (US {du:+.1f}%p, non-US {dn:+.1f}%p)")

    # 최악: 버린 공고가 전부 대조군이었다면. 대조군 상승폭이 커져 DiD 가 줄어든다.
    for label, assign in [("버린 것이 전부 non-US 였다면", "non-US"),
                          ("버린 것이 전부 US 였다면", "US")]:
        a = pre[(pre.region == assign) | (pre.region == "mixed/unknown")]
        c = post[(post.region == assign) | (post.region == "mixed/unknown")]
        d2 = rate(c) - rate(a)
        did = (du - d2) if assign == "non-US" else (d2 - dn)
        print(f"  {label:<28} DiD {did:+.1f}%p")

    print("\n  -> 두 극단 모두에서 부호가 유지되면 결론은 분류 방식에 의존하지 않는다.")


if __name__ == "__main__":
    main()
