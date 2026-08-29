"""
YouTube Analytics API -> 채널 진단 숫자.

조회수만 보면 뭘 고쳐야 할지 알 수 없다. 이 스크립트는 판단에 필요한 셋을 가져온다.
  1. 노출수 / 노출 클릭률(CTR)  -> 썸네일·제목 문제인가
  2. 평균 조회율(%)             -> 콘텐츠 문제인가
  3. 트래픽 소스                -> 알고리즘이 밀고 있는가

── 최초 1회 설정 ──────────────────────────────────────────────
1. console.cloud.google.com 에서 프로젝트 생성
2. 'API 및 서비스 > 라이브러리' 에서 아래 둘 사용 설정
     - YouTube Analytics API
     - YouTube Data API v3
3. 'OAuth 동의 화면': External / 테스트 모드,
   테스트 사용자에 채널을 관리하는 Google 계정 추가
4. '사용자 인증 정보 > OAuth 클라이언트 ID > 데스크톱 앱' 생성 후
   JSON 을 이 폴더에 client_secret.json 으로 저장
5. .venv/bin/python analytics.py
   -> 브라우저가 열리고 동의하면 token.json 이 생긴다 (이후 자동)

client_secret.json / token.json 은 .gitignore 에 있다. 절대 커밋하지 말 것.

usage:
  .venv/bin/python analytics.py            # 전체 기간
  .venv/bin/python analytics.py 2026-08-21 # 시작일 지정
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/youtube.readonly"]
SECRET = Path("client_secret.json")
TOKEN = Path("token.json")
OUT = Path("data/analytics")


def auth():
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not SECRET.exists():
                sys.exit(f"{SECRET} 가 없습니다. 파일 상단의 설정 절차를 먼저 진행하세요.")
            creds = InstalledAppFlow.from_client_secrets_file(
                str(SECRET), SCOPES).run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
    return creds


def query(yta, start, end, metrics, dimensions=None, sort=None):
    """실패해도 죽지 않는다. 지표 이름이 바뀌거나 권한이 없을 수 있다."""
    try:
        req = yta.reports().query(
            ids="channel==MINE", startDate=start, endDate=end,
            metrics=metrics,
            **({"dimensions": dimensions} if dimensions else {}),
            **({"sort": sort} if sort else {}))
        r = req.execute()
        cols = [h["name"] for h in r["columnHeaders"]]
        return pd.DataFrame(r.get("rows", []), columns=cols)
    except Exception as e:
        print(f"  [건너뜀] {metrics} — {str(e)[:160]}")
        return pd.DataFrame()


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else "2005-02-14"
    end = str(date.today() - timedelta(days=1))   # 오늘은 아직 집계 중
    creds = auth()
    yta = build("youtubeAnalytics", "v2", credentials=creds)
    yt = build("youtube", "v3", credentials=creds)

    titles = {}
    ch = yt.channels().list(part="contentDetails,statistics", mine=True).execute()
    stats = ch["items"][0]["statistics"]
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    for it in yt.playlistItems().list(part="snippet", playlistId=uploads,
                                      maxResults=50).execute().get("items", []):
        titles[it["snippet"]["resourceId"]["videoId"]] = it["snippet"]["title"]

    print("=" * 72)
    print(f"채널 누적  구독 {stats.get('subscriberCount')}명 · "
          f"조회 {stats.get('viewCount')}회 · 영상 {stats.get('videoCount')}개")
    print(f"집계 구간  {start} ~ {end}")
    print("=" * 72)

    # ---------- 1. 영상별 핵심 ----------
    core = query(yta, start, end,
                 "views,estimatedMinutesWatched,averageViewDuration,"
                 "averageViewPercentage,subscribersGained",
                 dimensions="video", sort="-views")
    if not core.empty:
        core["title"] = core["video"].map(titles).fillna(core["video"])
        core["watch_hours"] = (core["estimatedMinutesWatched"] / 60).round(1)
        core["sub_rate_%"] = (core["subscribersGained"] / core["views"] * 100).round(2)
        print("\n[1] 영상별")
        print(core[["title", "views", "watch_hours", "averageViewDuration",
                    "averageViewPercentage", "subscribersGained", "sub_rate_%"]]
              .to_string(index=False))

    # ---------- 2. 노출 / CTR ----------
    # 2026-01-15 에 Analytics API 에 추가된 지표. 이름이 바뀌면 위 [건너뜀] 이 뜬다
    imp = query(yta, start, end,
                "videoThumbnailImpressions,videoThumbnailImpressionsClickRate",
                dimensions="video", sort="-videoThumbnailImpressions")
    if not imp.empty:
        imp["title"] = imp["video"].map(titles).fillna(imp["video"])
        print("\n[2] 노출 / 클릭률")
        print(imp[["title", "videoThumbnailImpressions",
                   "videoThumbnailImpressionsClickRate"]].to_string(index=False))
        ctr = imp["videoThumbnailImpressionsClickRate"].iloc[0]
        print(f"\n  진단: CTR {ctr:.1f}%  "
              + ("→ 2% 미만. 썸네일·제목 문제" if ctr < 2 else
                 "→ 4~10% 정상 구간" if ctr >= 4 else "→ 2~4%. 개선 여지 있음"))

    # ---------- 3. 트래픽 소스 ----------
    tr = query(yta, start, end, "views",
               dimensions="insightTrafficSourceType", sort="-views")
    if not tr.empty:
        tr["비중%"] = (tr["views"] / tr["views"].sum() * 100).round(1)
        print("\n[3] 트래픽 소스")
        print(tr.to_string(index=False))
        algo = tr[tr["insightTrafficSourceType"]
                  .isin(["YT_SEARCH", "RELATED_VIDEO", "BROWSE_FEATURES"])]["views"].sum()
        print(f"\n  진단: 알고리즘 유입 {algo / tr['views'].sum() * 100:.0f}% "
              + ("→ 밀리기 시작함" if algo > 0 else "→ 아직 미노출. 외부 공유뿐"))

    # ---------- 4. 일자별 (추세) ----------
    daily = query(yta, start, end, "views,estimatedMinutesWatched,subscribersGained",
                  dimensions="day", sort="day")

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = end.replace("-", "")
    for name, df in [("videos", core), ("impressions", imp),
                     ("traffic", tr), ("daily", daily)]:
        if not df.empty:
            df.to_csv(OUT / f"{stamp}_{name}.csv", index=False)
    print(f"\n-> {OUT}/{stamp}_*.csv")


if __name__ == "__main__":
    main()
