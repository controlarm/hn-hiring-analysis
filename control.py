"""
대조군 체크: 'Who is hiring?'(구인) 감소가 진짜 채용 위축인가,
아니면 HN 스레드 자체의 인기 하락인가?

같은 whoishiring 계정이 매달 같이 올리는
'Who wants to be hired?'(구직) 스레드를 대조군으로 쓴다.
 - 둘 다 감소  -> 플랫폼 효과 (채용 이야기 못 함)
 - 구인만 감소 -> 진짜 수요 위축
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw_control")
ALGOLIA = "https://hn.algolia.com/api/v1"
UA = {"User-Agent": "hn-hiring-analysis/0.1"}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    hits, page = [], 0
    while True:
        d = requests.get(
            f"{ALGOLIA}/search_by_date",
            params={"tags": "story,author_whoishiring", "hitsPerPage": 1000, "page": page},
            headers=UA,
            timeout=30,
        ).json()
        hits += d["hits"]
        page += 1
        if page >= d["nbPages"]:
            break

    df = pd.DataFrame(hits)
    df["month"] = pd.to_datetime(df["created_at"], utc=True).dt.to_period("M")
    ctrl = df[df["title"].str.contains(r"wants to be hired", case=False, na=False)]
    print(f"구직 스레드 {len(ctrl)}개")

    rows = []
    for _, t in ctrl.iterrows():
        sid = t["objectID"]
        cache = RAW / f"{sid}.json"
        if cache.exists():
            d = json.loads(cache.read_text())
        else:
            d = requests.get(f"{ALGOLIA}/items/{sid}", headers=UA, timeout=60).json()
            cache.write_text(json.dumps(d))
            time.sleep(0.4)
        n = len([c for c in (d.get("children") or []) if c.get("text")])
        rows.append({"month": t["month"], "seekers": n})

    seek = pd.DataFrame(rows).groupby("month")["seekers"].sum()
    hire = pd.read_csv("data/volume.csv", index_col=0)["0"]
    hire.index = pd.PeriodIndex(hire.index, freq="M")

    both = pd.DataFrame({"구인": hire, "구직": seek}).dropna()
    both = both[both.index <= both.index.max() - 1]  # 진행 중인 달 제외
    both["구인/구직"] = (both["구인"] / both["구직"]).round(2)

    print("\n연도별 월평균")
    yr = both.groupby(both.index.year).mean().round(1)
    print(yr.to_string())

    for col in ["구인", "구직"]:
        pk = both[col].idxmax()
        print(
            f"\n{col}: 피크 {pk} {both[col].max():.0f}건"
            f" -> 최근12M {both[col].tail(12).mean():.0f}건"
            f" ({both[col].tail(12).mean() / both[col].max() - 1:+.0%})"
        )

    both.to_csv("data/hire_vs_seek.csv")
    print("\n-> data/hire_vs_seek.csv")


if __name__ == "__main__":
    main()
