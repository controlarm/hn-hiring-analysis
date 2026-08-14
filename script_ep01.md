# 1편 스크립트 — HN 채용글 15년치를 전부 세어봤습니다

- **길이** 약 8분 (한국어 나레이션 ≈ 2,600자 / 영어 ≈ 1,100 words)
- **화면** 차트 3장 + 텍스트 카드. 실사 B-roll 없음
- **원칙** 숫자는 전부 `README.md`의 계산과 일치. 한계는 숨기지 않고 앞에서 말한다

> 영어는 직역이 아니라 **영어로 자연스러운 문장**으로 따로 씁니다.
> 이 트랙은 님이 직접 다듬으세요 — 그게 이 채널의 영어 공부 파트입니다.

---

## 0:00 — 훅

**[화면]** 검은 화면에 숫자만. `972` → `273`

**KO**
2018년 5월, 어떤 채용 게시판에 한 달 동안 구인글이 972개 올라왔습니다.
지난달엔 273개였습니다.

테크 채용이 얼어붙었다는 얘기, 다들 들어보셨을 겁니다.
그런데 그걸 실제로 세어본 사람을 못 찾았습니다.

그래서 직접 셌습니다. 15년치, 9만 2천 730건.

**그런데 다 세고 나서 제일 놀란 건, 채용이 줄었다는 게 아니었습니다.**

**EN**
In May 2018, one job board got 972 job postings in a single month.
Last month, it got 273.

You've heard that tech hiring has frozen up. So have I.
But I couldn't find anyone who had actually counted.

So I did. Fifteen years. Ninety-two thousand, seven hundred and thirty job postings.

**And the thing that surprised me most wasn't that hiring fell.**

---

## 0:30 — 이 데이터가 뭐고, 뭐가 아닌지

**[화면]** 텍스트 카드 3줄

**KO**
데이터부터 말씀드릴게요.
해커뉴스에는 매달 1일 "Ask HN: Who is hiring?"이라는 글이 올라옵니다.
회사들이 댓글로 채용공고를 답니다. 2011년부터 한 달도 안 빠지고요.

182개월치를 전부 받아서, 댓글 하나를 공고 하나로 셌습니다.
공개 API고, 코드는 설명란에 있습니다. 직접 돌려보셔도 됩니다.

먼저 이건 짚고 갑니다.
**이 데이터는 전체 고용시장이 아닙니다.** 실리콘밸리 스타트업, 그리고 원격 채용에 심하게 치우친 표본입니다.
그러니까 앞으로 나올 숫자는 "테크 업계 전체"가 아니라 "이 바닥 한 조각"입니다.
그 조각이 꽤 선명하긴 합니다.

**EN**
Let's start with the data.
On the first of every month, Hacker News posts a thread called "Ask HN: Who is hiring?"
Companies reply with job postings. Every single month since 2011.

I pulled all 182 months and counted each top-level comment as one job posting.
It's a public API. The code is in the description. Run it yourself.

One caveat up front.
**This is not the whole job market.** It's a sample that leans hard toward Silicon Valley startups and remote-first companies.
So every number you're about to see describes one slice of tech — not all of it.
It's a pretty sharp slice, though.

---

## 1:15 — 1막 · 회사가 사라졌다

**[화면]** `1_volume` 차트 — 파란 선(구인)만 먼저 애니메이션

**KO**
자, 파란 선이 구인글입니다.

2018년 5월이 정점이에요. 972건.
2021년에 한 번 더 올라옵니다. 팬데믹 리바운드죠.
그리고 2022년부터 무너집니다.

최근 12개월 평균은 331건. **피크 대비 66% 감소입니다.**

여기까지는 예상하셨을 겁니다.
그런데 이 숫자를 그대로 믿으면 안 됩니다. 제가 안 믿었거든요.

**[화면]** 텍스트 카드: `채용이 준 건가, 해커뉴스가 시든 건가?`

**KO**
왜냐면 이 그래프는 두 가지로 설명이 됩니다.
하나, 진짜로 회사들이 사람을 덜 뽑는다.
둘, 그냥 해커뉴스라는 사이트 자체가 예전만 못하다.

두 번째가 맞다면 이 영상은 여기서 끝나야 합니다. 채용에 대해 아무것도 말할 수 없거든요.

그래서 대조군을 찾았습니다.

**EN**
The blue line is job postings.

The peak is May 2018 — 972 postings.
There's a second peak in 2021, the pandemic rebound.
Then from 2022, it falls apart.

The last twelve months average 331. **That's down 66% from the peak.**

You probably expected that.
But you shouldn't take that number at face value. I didn't.

**[SCREEN]** Text card: `Did hiring shrink — or did Hacker News?`

**EN**
Because this chart has two possible explanations.
One: companies really are hiring less.
Two: Hacker News just isn't the place it used to be.

If it's the second one, this video should end right here. The data would tell us nothing about hiring.

So I went looking for a control group.

---

## 2:25 — 대조군

**[화면]** `1_volume` — 주황 선(구직) 등장

**KO**
같은 날, 같은 계정이 스레드를 하나 더 올립니다.
"Who wants to be hired?" — 이번엔 **구직자**가 댓글을 답니다.

같은 사이트, 같은 계정, 같은 날짜.
사이트가 시들었다면 이 선도 같이 내려가야 합니다.

**[화면]** 주황 선 그려짐

**KO**
반대로 갑니다.

2018년에 월 93건이던 구직글이, 지금은 470건입니다. **5배가 됐어요.**
사이트는 시들지 않았습니다. 사람은 더 많이 왔습니다.
사라진 건 회사뿐입니다.

**[화면]** 교차 지점 강조 + 큰 숫자 `9.4 → 0.7`

**KO**
두 선은 2023년에 교차합니다.

구인글 하나당 구직글 몇 개인지로 보면 더 선명합니다.
2018년엔 구인이 구직의 **9.4배**였습니다. 회사가 사람을 못 구해서 안달이던 시절이죠.
지금은 **0.7배**입니다. 구직자가 더 많습니다.

13배가 뒤집힌 겁니다.

**EN**
On the same day, the same account posts a second thread.
"Who wants to be hired?" — this time, **job seekers** comment.

Same site, same account, same date.
If the site were dying, this line should fall too.

**[SCREEN]** Orange line draws in

**EN**
It does the opposite.

In 2018, that thread got 93 posts a month. Today it gets 470. **Five times more.**
The site isn't dying. More people are showing up than ever.
The only thing that disappeared is the employers.

**[SCREEN]** Highlight crossover + big number `9.4 → 0.7`

**EN**
The two lines cross in 2023.

The ratio makes it sharper.
In 2018, there were **9.4 job posts for every job seeker.** Companies were desperate.
Today it's **0.7.** Job seekers outnumber jobs.

That's a thirteen-fold swing.

---

## 3:40 — 2막 · 직업의 이름이 바뀌었다

**[화면]** `2_terms` 왼쪽 패널만

**KO**
자, 여기부터가 제가 안 예상했던 부분입니다.

공고 안에 어떤 단어가 들어있는지 세어봤습니다.
지금은 AI 붐이잖아요. 그러면 "머신러닝"이나 "데이터 사이언티스트" 같은 단어가 늘었어야 정상입니다.

**[화면]** 왼쪽 패널 선 그려짐

**KO**
반대입니다.

"machine learning"을 언급한 공고는 2017년 11.6%에서 지금 2.9%.
"data scientist"는 7.5%에서 1.8%.

**둘 다 4분의 1 토막입니다.**

AI가 제일 뜨거운 시기에, AI 관련 직함이 공고에서 사라진 거예요.

**[화면]** 오른쪽 패널 등장

**KO**
어디로 갔냐면, 여기로 갔습니다.

"LLM"은 2022년까지 이 데이터에 **한 번도** 안 나옵니다. 0퍼센트예요.
지금은 14.7%. 공고 일곱 개 중 하나입니다.

"AI agent"나 "agentic"도 마찬가지입니다. 2024년까지 사실상 없다가 지금 12.5%.

**[화면]** 두 패널 나란히

**KO**
수요가 사라진 게 아니었습니다. **이름이 갈린 겁니다.**

같은 회사가 2017년엔 "데이터 사이언티스트"를 뽑았고,
2026년엔 "LLM 엔지니어"를 뽑고 있습니다.

이게 왜 중요하냐면 — 키워드로 구직하는 사람은 이 전환을 놓칩니다.
"data scientist"로 알림 걸어두면, 지금 열려있는 자리의 대부분이 안 보입니다.

**EN**
Now here's the part I didn't see coming.

I counted which words appear inside the postings.
We're in an AI boom. So terms like "machine learning" and "data scientist" should be climbing.

**[SCREEN]** Left panel draws in

**EN**
They're doing the opposite.

Postings mentioning "machine learning" went from 11.6% in 2017 to 2.9% today.
"Data scientist" went from 7.5% to 1.8%.

**Both down about 75%.**

At the hottest moment for AI, the AI job titles vanished from the job posts.

**[SCREEN]** Right panel appears

**EN**
Here's where they went.

"LLM" does not appear **once** in this dataset before 2022. Zero percent.
Today it's 14.7% — roughly one posting in seven.

Same story for "AI agent" and "agentic." Basically nonexistent until 2024, now 12.5%.

**[SCREEN]** Both panels side by side

**EN**
The demand didn't disappear. **It got renamed.**

The same company that hired a "data scientist" in 2017
is hiring an "LLM engineer" in 2026.

And that matters, because if you job-hunt by keyword, you miss the switch.
Set an alert for "data scientist" and most of what's actually open never reaches you.

---

## 5:15 — 3막 · 회사가 파는 것도 바뀌었다

**[화면]** `3_worksetup`

**KO**
마지막으로, 공고가 **뭘 자랑하는지**를 봤습니다.

원격근무부터.
2019년엔 공고의 74%가 "onsite"였습니다. 사무실 출근이요.
2022년엔 21%까지 떨어집니다.

**[화면]** onsite 선 반등 구간 강조

**KO**
그런데 지금 34%입니다. **되돌아오고 있어요.**

"remote"는 2022년 초에 84.5%로 정점을 찍고 지금 54%입니다.
원격근무는 사라지진 않았지만, 확실히 정점은 지났습니다.

그리고 "hybrid"라는 단어. 2019년엔 1%였습니다. 사실상 없던 단어예요.
지금은 20% 근처입니다.

**[화면]** 실제 공고 문장 인용 카드

**KO**
그리고 이건 세다가 우연히 발견한 건데요.

2026년 공고의 9%가 "Claude"를 언급합니다. 열 개 중 하나 가까이요.
그래서 실제로 뭐라고 쓰여있나 열어봤습니다.

> "We are all-in on Claude Code for scoping and shipping. You get a seat on Day 1."

요구 스킬이 아니었습니다. **복지처럼 쓰고 있었어요.**

예전에 공고가 맥북이랑 스탠딩 데스크를 자랑하던 자리에,
지금은 AI 코딩 툴이 들어가 있습니다.

**EN**
Finally, I looked at what the postings are **selling.**

Start with remote work.
In 2019, 74% of postings said "onsite."
By 2022, that dropped to 21%.

**[SCREEN]** Highlight the onsite rebound

**EN**
Today it's back to 34%. **It's coming back.**

"Remote" peaked at 84.5% in early 2022 and sits at 54% now.
Remote work hasn't gone away — but it's clearly past its peak.

And "hybrid"? It was 1% in 2019. The word barely existed.
Now it's around 20%.

**[SCREEN]** Quote card from a real posting

**EN**
And here's something I stumbled into while counting.

9% of 2026 postings mention "Claude." Nearly one in ten.
So I opened them up to see what they actually said.

> "We are all-in on Claude Code for scoping and shipping. You get a seat on Day 1."

It wasn't listed as a required skill. **They're using it as a perk.**

The slot in the job post that used to brag about MacBooks and standing desks
is now occupied by AI coding tools.

---

## 6:45 — 한계

**[화면]** 텍스트 카드 4줄

**KO**
믿기 전에 알아야 할 것들입니다.

하나. 아까 말씀드린 표본 편향. 실리콘밸리, 스타트업, 원격 쪽으로 심하게 기울어 있습니다.

둘. 단어를 셌다는 건 맥락을 못 본다는 뜻입니다.
방금 Claude 사례가 정확히 그 예시예요. 언급됐다고 요구 스킬은 아닙니다.
그래서 "go"나 "agent" 같은 애매한 단어는 각각 "golang", "agentic"으로 좁혔습니다.

셋. 상승 중인 단어에 "정점 대비 몇 퍼센트 하락" 같은 건 계산하면 안 됩니다.
아직 정점이 안 왔으니까요. 분석하다가 실제로 한 번 걸렸습니다.

넷. 이건 미국 데이터입니다. 한국 채용시장은 이 곡선을 안 따릅니다.

**EN**
Before you believe any of this, here's what's wrong with it.

One. The sample bias I mentioned. Heavily skewed toward Silicon Valley, startups, and remote-first companies.

Two. Counting words means missing context.
The Claude example is exactly that — a mention is not a requirement.
That's why ambiguous terms got narrowed: "go" became "golang," "agent" became "agentic."

Three. You can't compute "down X% from peak" for a term that's still rising.
The peak hasn't happened yet. I made that mistake once during the analysis.

Four. This is US data. The Korean job market does not follow this curve.

---

## 7:30 — 마무리

**[화면]** 세 차트 요약

**KO**
정리하면 세 줄입니다.

회사는 3분의 1로 줄었고, 지원자는 5배가 됐습니다.
AI 수요는 늘었지만 그걸 부르는 이름이 바뀌었습니다.
그리고 회사들은 이제 AI 툴을 복지처럼 팝니다.

데이터랑 코드는 전부 설명란에 있습니다. 다르게 잘라보시면 저랑 다른 결론이 나올 수도 있어요. 나오면 댓글로 알려주세요.

**[화면]** 다음 편 티저 — 비자 그래프 살짝

**KO**
다음 편에는 이 데이터에서 하나 더 파볼 게 있습니다.
비자를 언급하는 공고 비율이 2018년 11.8%에서 2025년 3.5%까지 떨어졌다가,
올해 다시 올라오고 있거든요.

왜 올라오는지, 다음 편에서 세어보겠습니다.

**EN**
Three lines, then.

Employers shrank to a third. Applicants grew fivefold.
AI demand went up, but the words for it changed completely.
And companies now sell AI tools the way they used to sell free lunch.

All the data and code is in the description. Slice it differently and you might reach a different conclusion. If you do, tell me in the comments.

**[SCREEN]** Next-episode teaser — visa chart, brief

**EN**
There's one more thing buried in this data.
The share of postings mentioning visas fell from 11.8% in 2018 to 3.5% in 2025 —
and this year, it's climbing back.

Next time, I'll count why.

---
---

# 제작 노트

## 제목 후보

| | 한국어 | English |
|---|---|---|
| A | 채용공고 9만 건을 세어봤더니, 직업 이름이 바뀌어 있었다 | I counted 92,730 job posts. The jobs didn't vanish — they got renamed. |
| B | "데이터 사이언티스트"는 어디로 갔나 — 공고 15년치 전수 분석 | Where did "data scientist" go? 15 years of job posts, counted. |
| C | 테크 채용 -66%. 그런데 지원자는 5배가 됐다 | Tech hiring is down 66%. Applicants are up 5x. |

→ **A 추천.** 반전이 제목 안에 있고, 숫자가 구체적이라 낚시로 안 읽힙니다.
B는 검색 유입용이라 2순위로 A/B 테스트하기 좋습니다.

## 썸네일

`2_terms` 왼쪽 패널의 추락하는 선 하나만 크게 + 텍스트 두 줄:
`"data scientist"` / `-76%`
차트를 그대로 쓰지 말고 **선 하나만** 잘라 쓰세요. 썸네일에서 4개 선은 안 읽힙니다.

## 챕터 (설명란)

```
0:00 972개에서 273개로
0:30 이 데이터가 뭐고, 뭐가 아닌지
1:15 회사가 사라졌다
2:25 그런데 지원자는 5배가 됐다
3:40 직업의 이름이 바뀌었다
5:15 회사가 파는 것도 바뀌었다
6:45 이 분석의 한계
7:30 다음 편: 비자
```

## 설명란 템플릿

```
해커뉴스 'Ask HN: Who is hiring?' 스레드 182개월치, 채용공고 92,730건을
전수 수집해서 분석했습니다.

분석 코드 + 데이터: github.com/<계정>/hn-hiring-analysis
직접 돌려보실 수 있습니다. 다른 결론이 나오면 댓글로 알려주세요.

데이터: Hacker News (Algolia API, 공개)
기간: 2011.04 – 2026.07
```

## TTS / 더빙

- 한국어·영어 **같은 보이스 계열**로 통일 (채널 목소리 = 정체성)
- 속도 0.95x 정도. 숫자가 많아서 기본 속도는 빠르게 들립니다
- 굵게 표시한 문장 앞뒤로 **0.4초 무음** 삽입 — 숫자가 꽂히는 지점입니다
- `972`, `9.4`, `0.7` 같은 숫자는 TTS가 잘못 읽는 경우가 있으니 렌더 후 반드시 청취 확인

## 프레임 (`out/frames/dark/` 또는 `light/`)

`.venv/bin/python frames.py` 로 생성. **번호 순서 = 영상 순서.** Vrew에 순서대로 끌어다 놓으면 됩니다.

| 파일 | 대본 위치 | 나레이션 |
|---|---|---|
| `01_hook` | 0:00 | 972 → 273 |
| `02_data` | 0:30 | 데이터 출처 + 표본 편향 |
| `03_ch1a_hire` | 1:15 | "파란 선이 구인글입니다" |
| `04_ch1b_peak` | 1:25 | "2018년 5월이 정점, 972건" |
| `05_question` | 1:55 | "채용이 준 건가, HN이 시든 건가" |
| `06_ch1c_control` | 2:25 | "같은 날 같은 계정이 스레드를 하나 더" |
| `07_ch1d_cross` | 3:05 | "두 선은 2023년에 교차합니다" |
| `07b_ratio` | 3:20 | "9.4배에서 0.7배. 13배가 뒤집혔다" |
| `08_ch2a_old` | 3:50 | "반대입니다" (오른쪽 비워둠 = 다음 컷 예고) |
| `09_ch2b_both` | 4:30 | "어디로 갔냐면, 여기로" |
| `10_ch3a_onsite` | 5:15 | "2019년엔 74%가 onsite" |
| `11_ch3b_remote` | 5:35 | "원격은 2022년 초 정점" |
| `12_ch3c_hybrid` | 5:55 | "hybrid는 2019년엔 없던 단어" |
| `13_quote` | 6:15 | 실제 공고 인용 — **여기서 3초 정지** |
| `14_limits` | 6:45 | 한계 4가지 |
| `15_summary` | 7:30 | 정리 3줄 |
| `16_teaser` | 7:45 | 다음 편 비자 |

컷 전환은 **크로스페이드 0.3초**. 08 → 09는 왼쪽 패널 위치가 같아서 오른쪽만 나타나는 것처럼 보입니다.

나중에 진짜 선 그리기 애니메이션이 필요하면 matplotlib `FuncAnimation`으로 mp4를 뽑으면 되는데, 1편에는 과합니다.

## 영어 트랙 — 이번 편 표현 8개

| 표현 | 뜻 | 어디에 |
|---|---|---|
| take it at face value | 액면 그대로 믿다 | 1막 |
| a control group | 대조군 | 1막 |
| outnumber | 수적으로 앞서다 | 대조군 |
| a thirteen-fold swing | 13배 반전 | 대조군 |
| I didn't see that coming | 예상 못 했다 | 2막 |
| past its peak | 정점을 지난 | 3막 |
| stumble into something | 우연히 발견하다 | 3막 |
| skewed toward ~ | ~쪽으로 치우친 | 한계 |

영어 트랙 녹음/렌더 전에 이 8개를 소리내어 읽어보세요. 그게 이 채널의 영어 공부 파트입니다.
