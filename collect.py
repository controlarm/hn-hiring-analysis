"""
HN "Ask HN: Who is hiring?" 월간 스레드 수집기.

- Algolia HN API (무료, 키 불필요)
- 스레드 원본 JSON은 data/raw/ 에 캐시 -> 재실행하면 새 달만 받아옴
- 최상위 댓글 1개 = 채용공고 1건

usage: .venv/bin/python collect.py
"""

import html
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests

RAW = Path("data/raw")
OUT = Path("data")
ALGOLIA = "https://hn.algolia.com/api/v1"
UA = {"User-Agent": "hn-hiring-analysis/0.1"}

TAG_RE = re.compile(r"<[^>]+>")


def list_threads() -> pd.DataFrame:
    """whoishiring 계정이 올린 'Who is hiring?' 스레드 목록."""
    hits, page = [], 0
    while True:
        r = requests.get(
            f"{ALGOLIA}/search_by_date",
            params={
                "tags": "story,author_whoishiring",
                "hitsPerPage": 1000,
                "page": page,
            },
            headers=UA,
            timeout=30,
        )
        r.raise_for_status()
        d = r.json()
        hits += d["hits"]
        page += 1
        if page >= d["nbPages"]:
            break

    df = pd.DataFrame(hits)
    # "Who wants to be hired?", "Freelancer?" 스레드는 제외
    df = df[df["title"].str.contains(r"Who is hiring\?", case=False, na=False)]
    df["month"] = pd.to_datetime(df["created_at"]).dt.tz_convert("UTC").dt.to_period("M")
    df = df[["objectID", "month", "title", "num_comments"]].sort_values("month")
    return df.reset_index(drop=True)


def fetch_thread(story_id: str) -> dict:
    """스레드 전체 트리를 1회 요청으로. 이미 받은 건 캐시에서."""
    cache = RAW / f"{story_id}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    r = requests.get(f"{ALGOLIA}/items/{story_id}", headers=UA, timeout=60)
    r.raise_for_status()
    d = r.json()
    cache.write_text(json.dumps(d))
    time.sleep(0.4)  # 예의상 rate limit
    return d


def clean(text: str) -> str:
    """HN 댓글 HTML -> 평문."""
    if not text:
        return ""
    t = text.replace("<p>", "\n").replace("</p>", "\n")
    t = TAG_RE.sub(" ", t)
    return html.unescape(t).strip()


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)

    threads = list_threads()
    print(f"스레드 {len(threads)}개 ({threads['month'].min()} ~ {threads['month'].max()})")

    rows = []
    for i, t in threads.iterrows():
        d = fetch_thread(t["objectID"])
        # 최상위 자식만 = 채용공고. 삭제된 댓글은 text=None
        posts = [c for c in (d.get("children") or []) if c.get("text")]
        for c in posts:
            rows.append(
                {
                    "month": str(t["month"]),
                    "story_id": t["objectID"],
                    "comment_id": c["id"],
                    "author": c.get("author"),
                    "text": clean(c["text"]),
                }
            )
        if i % 20 == 0 or i == len(threads) - 1:
            print(f"  [{i + 1}/{len(threads)}] {t['month']}  공고 {len(posts)}건")

    df = pd.DataFrame(rows)
    df["n_chars"] = df["text"].str.len()
    OUT.mkdir(exist_ok=True)
    df.to_parquet(OUT / "posts.parquet", index=False)

    print(f"\n총 공고 {len(df):,}건 -> data/posts.parquet")
    print(df.groupby("month").size().tail(12).to_string())


if __name__ == "__main__":
    main()
