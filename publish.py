"""
발행 도구 — 업로드된 영상의 메타데이터/썸네일을 고친다.

videos.update 는 snippet 을 **통째로 교체**한다. categoryId 만 보내면
제목·설명·태그가 전부 지워진다. 그래서 이 스크립트는 반드시
  1) 현재 snippet 을 읽고
  2) 백업을 남기고
  3) 바꿀 필드만 덮어써서
  4) 전체를 다시 보낸다.
직접 videos().update() 를 호출하지 말 것.

인증은 analytics.py 와 같은 token.json 을 쓴다(force-ssl 스코프 포함).

usage:
  .venv/bin/python publish.py --video Wht34-0Gg_Y --category 22
  .venv/bin/python publish.py --video XTcukQKfUyE --append-desc "1편 링크..."
  .venv/bin/python publish.py --video XTcukQKfUyE --thumbnail out/thumb/thumb_a.png
  .venv/bin/python publish.py --video XTcukQKfUyE --restore data/video_backup/xxx.json
"""

import argparse
import json
from datetime import date
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from analytics import auth

BACKUP = Path("data/video_backup")
# snippet 중 쓰기 가능한 필드만. 나머지(channelId, thumbnails...)를 되보내면 거절된다.
WRITABLE = ["title", "description", "tags", "categoryId",
            "defaultLanguage", "defaultAudioLanguage"]


def fetch(yt, vid):
    r = yt.videos().list(part="snippet,status", id=vid).execute()
    if not r["items"]:
        raise SystemExit(f"영상을 찾을 수 없습니다: {vid}")
    return r["items"][0]


def backup(item, vid):
    BACKUP.mkdir(parents=True, exist_ok=True)
    p = BACKUP / f"{vid}_{date.today():%Y%m%d}.json"
    if p.exists():                        # 같은 날 두 번 고쳐도 원본을 덮지 않는다
        p = BACKUP / f"{vid}_{date.today():%Y%m%d}_{len(list(BACKUP.glob('*')))}.json"
    p.write_text(json.dumps(item, ensure_ascii=False, indent=2))
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--category")
    ap.add_argument("--title")
    ap.add_argument("--desc", help="설명 전체 교체. 파일 경로면 파일 내용을 쓴다")
    ap.add_argument("--append-desc", help="설명 끝에 덧붙인다")
    ap.add_argument("--tags", help="쉼표 구분")
    ap.add_argument("--lang", help="defaultLanguage/defaultAudioLanguage (예: ko)")
    ap.add_argument("--thumbnail")
    ap.add_argument("--privacy", choices=["private", "unlisted", "public"])
    ap.add_argument("--restore", help="백업 JSON 으로 snippet 되돌리기")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    yt = build("youtube", "v3", credentials=auth())
    item = fetch(yt, a.video)
    snip = item["snippet"]
    print(f"대상: {snip['title'][:50]}")
    p = backup(item, a.video)
    print(f"백업: {p}")

    new = {k: snip[k] for k in WRITABLE if k in snip}

    if a.restore:
        old = json.loads(Path(a.restore).read_text())["snippet"]
        new = {k: old[k] for k in WRITABLE if k in old}
        print("  복원 모드")
    if a.category:
        print(f"  categoryId  {new.get('categoryId')} -> {a.category}")
        new["categoryId"] = a.category
    if a.title:
        print(f"  title       -> {a.title}")
        new["title"] = a.title
    if a.desc:
        t = Path(a.desc).read_text() if Path(a.desc).exists() else a.desc
        print(f"  description 교체 ({len(new.get('description',''))} -> {len(t)}자)")
        new["description"] = t
    if a.append_desc:
        new["description"] = new.get("description", "").rstrip() + "\n\n" + a.append_desc
        print(f"  description 뒤에 {len(a.append_desc)}자 추가")
    if a.tags:
        new["tags"] = [t.strip() for t in a.tags.split(",") if t.strip()]
        print(f"  tags        -> {len(new['tags'])}개")
    if a.lang:
        # Studio 업로드본은 이 둘이 비어 있다. 비면 자막·번역 기능이 언어를 못 잡는다
        new["defaultLanguage"] = new["defaultAudioLanguage"] = a.lang
        print(f"  language    -> {a.lang}")

    if a.dry_run:
        print("\n[dry-run] 아래를 보낼 예정:")
        print(json.dumps(new, ensure_ascii=False, indent=2)[:1200])
        return

    if new != {k: snip[k] for k in WRITABLE if k in snip}:
        yt.videos().update(part="snippet",
                           body={"id": a.video, "snippet": new}).execute()
        print("-> snippet 반영됨")
    else:
        print("-> snippet 변경 없음")

    if a.privacy:
        # status 는 snippet 과 별개 part 라 따로 보낸다. 여기도 통째 교체이므로
        # 기존 status 를 읽어 privacyStatus 만 갈아끼운다
        st = {k: v for k, v in item["status"].items()
              if k in ("privacyStatus", "selfDeclaredMadeForKids",
                       "embeddable", "license", "publicStatsViewable")}
        print(f"  privacyStatus  {st.get('privacyStatus')} -> {a.privacy}")
        st["privacyStatus"] = a.privacy
        yt.videos().update(part="status",
                           body={"id": a.video, "status": st}).execute()
        print("-> 공개 범위 반영됨")

    if a.thumbnail:
        yt.thumbnails().set(videoId=a.video,
                            media_body=MediaFileUpload(a.thumbnail)).execute()
        print(f"-> 썸네일 반영됨: {a.thumbnail}")


if __name__ == "__main__":
    main()
