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

import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# force-ssl 은 읽기에 필요 없다. 발행(videos.update / thumbnails.set)용으로 미리 받아둔다.
# 스코프를 나중에 늘리면 동의를 또 받아야 하는데, 테스트 모드에서는 그게 잦아진다.
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
# 이 구글 계정에는 개인 채널도 붙어 있다. 동의 화면에서 잘못 고르면
# 엉뚱한 채널 숫자를 보게 되므로, 인증 직후 채널을 대조한다.
CHANNEL_ID = "UCJ7gCTc6xZW1Uw1do5dMywA"      # 대조군
SECRET = Path("client_secret.json")
TOKEN = Path("token.json")
OUT = Path("data/analytics")


def consent():
    """브라우저를 열어 새로 동의받는다."""
    if not SECRET.exists():
        sys.exit(f"{SECRET} 가 없습니다. 파일 상단의 설정 절차를 먼저 진행하세요.")
    print("브라우저에서 구글 계정 동의가 필요합니다...")
    return InstalledAppFlow.from_client_secrets_file(
        str(SECRET), SCOPES).run_local_server(port=0)


def auth():
    creds = None
    if TOKEN.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
        except ValueError:
            creds = None            # 스코프가 늘어나면 기존 토큰은 못 쓴다
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                # OAuth 앱이 '테스트' 상태면 리프레시 토큰이 7일 만에 만료된다.
                # 구글 정책이라 코드로 못 막는다. 만료되면 그냥 다시 동의받는다.
                print("토큰이 만료됐습니다(테스트 모드는 7일). 다시 동의받습니다.")
                creds = consent()
        else:
            creds = consent()
        TOKEN.write_text(creds.to_json())
    return creds


def query(yta, start, end, metrics, dimensions=None, sort=None,
          filters=None, max_results=200):
    """실패해도 죽지 않는다. 지표 이름이 바뀌거나 권한이 없을 수 있다."""
    try:
        req = yta.reports().query(
            ids="channel==MINE", startDate=start, endDate=end,
            metrics=metrics,
            **({"dimensions": dimensions} if dimensions else {}),
            **({"sort": sort} if sort else {}),
            **({"filters": filters} if filters else {}),
            # video 차원 리포트는 maxResults 가 없으면 거절된다
            **({"maxResults": max_results} if dimensions == "video" else {}))
        r = req.execute()
        cols = [h["name"] for h in r["columnHeaders"]]
        return pd.DataFrame(r.get("rows", []), columns=cols)
    except Exception as e:
        print(f"  [건너뜀] {metrics} — {str(e)[:160]}")
        return pd.DataFrame()


def video_seconds(yt, vid):
    """ISO8601 재생시간 -> 초. 지속 곡선의 x축을 실제 시각으로 바꾸기 위함."""
    d = yt.videos().list(part="contentDetails", id=vid).execute()
    iso = d["items"][0]["contentDetails"]["duration"]
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    h, mi, se = (int(g or 0) for g in m.groups())
    return h * 3600 + mi * 60 + se


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else "2005-02-14"
    end = str(date.today() - timedelta(days=1))   # 오늘은 아직 집계 중
    creds = auth()
    yta = build("youtubeAnalytics", "v2", credentials=creds)
    yt = build("youtube", "v3", credentials=creds)

    titles = {}
    ch = yt.channels().list(part="snippet,contentDetails,statistics",
                            mine=True).execute()
    got = ch["items"][0]
    if got["id"] != CHANNEL_ID:
        TOKEN.unlink(missing_ok=True)
        sys.exit(
            f"\n잘못된 채널로 인증됐습니다: '{got['snippet']['title']}' ({got['id']})\n"
            f"필요한 채널: '대조군' ({CHANNEL_ID})\n\n"
            "토큰을 지웠습니다. 다시 실행한 뒤 동의 화면에서\n"
            "'대조군' 채널을 선택하세요 (개인 채널 아님).")
    stats = got["statistics"]
    uploads = got["contentDetails"]["relatedPlaylists"]["uploads"]
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

    # ---------- 2. 시청 지속 곡선 ----------
    # 어디서 이탈하는지가 조회수보다 훨씬 중요하다.
    # 노출/CTR(videoThumbnailImpressions)은 reports.query 가 지원하지 않는다.
    # "The query is not supported" 로 거절되므로 Studio 도달범위 탭에서 직접 확인할 것.
    imp = pd.DataFrame()
    for vid, title in titles.items():
        ret = query(yta, start, end,
                    "audienceWatchRatio,relativeRetentionPerformance",
                    dimensions="elapsedVideoTimeRatio", filters=f"video=={vid}")
        if ret.empty:
            continue
        length = video_seconds(yt, vid)
        print(f"\n[2] 시청 지속 곡선 — {title}")
        for i in range(0, len(ret), max(1, len(ret) // 12)):
            r = ret.iloc[i]
            s = int(r["elapsedVideoTimeRatio"] * length)
            bar = "█" * int(r["audienceWatchRatio"] * 40)
            print(f"    {s // 60}:{s % 60:02d}  {r['audienceWatchRatio'] * 100:5.1f}%  {bar}")
        early = ret[ret["elapsedVideoTimeRatio"] <= 0.06]["audienceWatchRatio"]
        if len(early) >= 2:
            drop = (early.iloc[0] - early.iloc[-1]) * 100
            print(f"\n  진단: 첫 {int(0.06 * length)}초에 {drop:.0f}%p 이탈  "
                  + ("→ 훅 문제. 도입부를 다시 설계할 것" if drop > 40 else "→ 정상 범위"))

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
