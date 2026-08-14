# HN "Who is hiring?" 15년치 분석 — 1편

Hacker News의 월간 채용 스레드 `Ask HN: Who is hiring?` **182개월 / 공고 92,730건**을
전수 수집해서 채용 수요와 요구 스킬의 변화를 측정한다.

데이터는 전부 공개 API(Algolia HN Search, 키 불필요)에서 온다. 사유 데이터 없음.

## 실행

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python pandas matplotlib requests pyarrow pillow
```

### 분석

```bash
.venv/bin/python collect.py    # 구인 스레드 수집 (data/raw/ 에 캐시, 재실행 시 새 달만)
.venv/bin/python control.py    # 대조군: 구직 스레드 수집
.venv/bin/python analyze.py    # 키워드 침투율 시계열
.venv/bin/python charts.py     # 차트 3종 -> out/ (라이트/다크, 1920x1080)
```

### 영상 (ffmpeg 필요)

```bash
.venv/bin/python frames.py                  # 프레임 18장 -> out/frames/{light,dark}/
.venv/bin/python thumbnail.py               # 썸네일 2안 + 피드 크기 미리보기
.venv/bin/python build_video.py --silent    # 무음 프리뷰 (키 없이 흐름 확인)

export ELEVENLABS_API_KEY="sk_..."
export ELEVENLABS_VOICE_ID="..."
.venv/bin/python render_audio.py            # 나레이션 -> out/audio/*.mp3
.venv/bin/python build_video.py             # 완성본 -> out/ep01.mp4
```

**대본은 `narration.py` 한 곳에만 있다.** 한 장면을 고쳤으면
그 `out/audio/<stem>.mp3` 만 지우고 `render_audio.py` → `build_video.py` 를 다시 돌린다.
나머지는 캐시에서 재사용되므로 몇 초면 끝난다.

## 방법

- **1공고 = 스레드의 최상위 댓글 1개.** 대댓글은 질문/잡담이라 제외.
- **침투율 = 그 달 공고 중 해당 단어를 언급한 비율(%).** 공고 수 변동에 영향받지 않게 정규화.
- **진행 중인 달은 제외.** 매달 1일에 스레드가 열리므로 마지막 달은 항상 미완성.
- **대조군.** 같은 계정(`whoishiring`)이 같은 날 올리는 `Who wants to be hired?`(구직)
  스레드를 대조군으로 둔다. 구인 감소가 HN 자체의 인기 하락 때문인지 구분하기 위함.

## 알려진 한계

- HN은 실리콘밸리 스타트업·원격 채용에 크게 치우친 표본이다. **전체 고용시장이 아니다.**
- 단어 매칭은 맥락을 모른다. `go`(일반 단어), `agent`(보험/에이전시),
  `prompt`(prompt payment)는 오탐이 많아 각각 `golang`, `agentic|ai agent`,
  `prompt engineer`로 좁혔다. 검증 결과는 아래.
- 상승 중인 단어에 "피크 대비 %"를 쓰면 안 된다. 아직 정점을 안 지났기 때문.
- 언급 = 요구 스킬이라는 보장은 없다. "우리는 Claude Code를 씁니다" 같은 문화 어필도 섞인다.

### 오탐 검증 (`claude`)

프랑스 이름 Claude와 섞일 수 있어 2026년 매칭 129건 중 12건을 육안 확인 →
**전부 Anthropic Claude 관련, 오탐 0건.** 다만 대부분 요구 스킬이 아니라
"우리는 Claude Code로 개발한다"는 툴/문화 어필이었다.

## 결과 요약

| | 2017–18 | 2026 |
|---|---|---|
| 월평균 구인글 | 808 (피크 972) | 331 (**−66%**) |
| 월평균 구직글 | 93 | 470 (**5배**) |
| 구인/구직 비율 | 9.4 | **0.7** |
| `machine learning` | 11.6% | 2.9% (−75%) |
| `data scientist` | 7.5% | 1.8% (−76%) |
| `LLM` | 0% | 14.7% |
| `AI agent / agentic` | 0% | 12.5% |
| `onsite` | 74.5% | 34.1% (2022년 21%까지 하락 후 반등) |
| `remote` | 30.3% | 54.2% (2022년 84.5% 정점) |

## 파일

| | |
|---|---|
| `collect.py` | 구인 스레드 수집 → `data/posts.parquet` |
| `control.py` | 구직 스레드 대조군 → `data/hire_vs_seek.csv` |
| `analyze.py` | 키워드 침투율 → `data/keyword_share.csv`, `data/volume.csv` |
| `charts.py` | 차트 3종 → `out/` |
| `frames.py` | 영상용 프레임 18장 (번호 순서 = 영상 순서) |
| `thumbnail.py` | 썸네일 2안 + 피드 크기(350px) 미리보기 |
| `narration.py` | **대본 원본.** 프레임별 나레이션 + hold 시간 |
| `render_audio.py` | 나레이션 → ElevenLabs multilingual v2 → mp3 |
| `build_video.py` | 프레임 + 오디오 → `out/ep01.mp4` |
| `script_ep01.md` | 대본 한/영 + 제목·썸네일·챕터·설명란 |
| `data/raw/` | 스레드 원본 JSON 캐시 (재실행 시 API 재호출 안 함) |
