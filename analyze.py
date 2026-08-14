"""
수집한 HN 채용공고에서 스토리 찾기 (숫자만, 차트는 나중에).

usage: .venv/bin/python analyze.py
"""

import re

import pandas as pd

pd.set_option("display.width", 200)

# 정규식 모호성 주의:
#   - "go"는 일반 단어와 충돌 -> golang만
#   - "agent"는 보험/에이전시와 충돌 -> agentic / ai agent 만
#   - "prompt"는 "prompt payment"와 충돌 -> prompt engineer만
TERMS = {
    # --- LLM 시대 ---
    "LLM": r"\bllms?\b",
    "GenAI": r"\bgen(erative )?[- ]?ai\b",
    "RAG": r"\brag\b|retrieval[- ]augmented",
    "Agentic": r"\bagentic\b|\bai agents?\b",
    "Prompt eng": r"prompt engineer",
    "Fine-tuning": r"fine[- ]?tun",
    "Vector DB": r"vector (database|db|search|store)|\bpinecone\b|\bweaviate\b",
    "OpenAI": r"\bopenai\b",
    "Anthropic/Claude": r"\banthropic\b|\bclaude\b",
    "LangChain": r"\blangchain\b|\bllamaindex\b",
    "Transformer": r"\btransformers?\b",
    "MLOps": r"\bmlops\b",
    # --- 이전 ML 시대 ---
    "Machine learning": r"machine learning\b",
    "Deep learning": r"deep learning\b",
    "Data scientist": r"data scientists?\b",
    "NLP": r"\bnlp\b|natural language processing",
    "Computer vision": r"computer vision\b|\bcv engineer",
    "PyTorch": r"\bpytorch\b",
    "TensorFlow": r"\btensorflow\b",
    # --- 빅데이터 시대 ---
    "Hadoop": r"\bhadoop\b",
    "Spark": r"\bspark\b",
    "Kafka": r"\bkafka\b",
    "ETL": r"\betl\b",
    "Data engineer": r"data engineers?\b",
    "Airflow/dbt": r"\bairflow\b|\bdbt\b",
    "Snowflake/DBX": r"\bsnowflake\b|\bdatabricks\b",
    # --- 언어/인프라 ---
    "Python": r"\bpython\b",
    "TypeScript": r"\btypescript\b",
    "JavaScript": r"\bjavascript\b",
    "Rust": r"\brust\b",
    "Golang": r"\bgolang\b",
    "Java": r"\bjava\b",
    "Ruby/Rails": r"\bruby\b|\brails\b",
    "PHP": r"\bphp\b",
    "Scala": r"\bscala\b",
    "React": r"\breact(\.js|js)?\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Docker": r"\bdocker\b",
    "Terraform": r"\bterraform\b",
    "AWS": r"\baws\b",
    # --- 근무형태 ---
    "Remote": r"\bremote\b",
    "Onsite": r"\bonsite\b|\bon-site\b",
    "Hybrid": r"\bhybrid\b",
    "Visa": r"\bvisa\b|\bh1-?b\b|\bh-1b\b",
    "Relocation": r"\brelocat",
    # --- 시니어리티 ---
    "Senior": r"\bsenior\b|\bsr\.?\b",
    "Staff/Principal": r"\bstaff engineer\b|\bprincipal engineer\b",
    "Junior/Entry": r"\bjunior\b|\bentry[- ]level\b|\bnew grad",
    "Intern": r"\binterns?(hip)?\b",
    "PhD": r"\bph\.?d\b",
    # --- 지나간 유행 ---
    "Crypto/Web3": r"\bcrypto\b|\bweb3\b|\bblockchain\b|\bethereum\b|\bsolidity\b",
}


def main() -> None:
    df = pd.read_parquet("data/posts.parquet")
    df["month"] = pd.PeriodIndex(df["month"], freq="M")

    # 2026-08 스레드는 아직 진행 중 -> 제외
    last_full = df["month"].max() - 1
    df = df[df["month"] <= last_full]
    lo = df["month"].min()

    print("=" * 78)
    print(f"HN 'Who is hiring?'  {lo} ~ {last_full}   공고 {len(df):,}건")
    print("=" * 78)

    # ---------- 1. 채용 볼륨 ----------
    vol = df.groupby("month").size()
    yearly = vol.groupby(vol.index.year).mean().round(0).astype(int)
    peak_m, peak_v = vol.idxmax(), vol.max()
    recent = vol.tail(12).mean()

    print("\n[1] 월평균 공고 수 (연도별)")
    print(yearly.to_string())
    print(f"\n  피크      : {peak_m}  {peak_v}건")
    print(f"  최근 12개월: {recent:.0f}건  (피크 대비 {recent / peak_v - 1:+.0%})")

    # ---------- 2. 키워드 침투율 ----------
    text = df["text"].str.lower()
    pen = pd.DataFrame(
        {
            name: text.str.contains(pat, regex=True, na=False)
            for name, pat in TERMS.items()
        }
    )
    pen["month"] = df["month"].values
    share = pen.groupby("month").mean() * 100  # 그 달 공고 중 언급 %

    now = share.tail(12).mean()  # 최근 12개월 평균
    peak = share.max()
    peak_when = share.idxmax()
    base19 = share[share.index.year == 2019].mean()  # LLM 이전 기준선

    tbl = pd.DataFrame(
        {
            "지금(%)": now.round(1),
            "2019(%)": base19.round(1),
            "피크(%)": peak.round(1),
            "피크시점": peak_when.astype(str),
            "피크대비": (now / peak.replace(0, pd.NA) - 1).mul(100).round(0),
        }
    )

    print("\n[2] 새로 뜬 것  — 2019년엔 없다가 지금 있는 것 (지금 - 2019, 상위 12)")
    print(tbl.assign(변화=(now - base19).round(1)).nlargest(12, "변화").to_string())

    print("\n[3] 사라진 것  — 2019년 대비 가장 많이 빠진 것 (하위 12)")
    print(tbl.assign(변화=(now - base19).round(1)).nsmallest(12, "변화").to_string())

    print("\n[4] 정점을 지난 것 — 피크 대비 -50% 이상 빠졌고 한때 5% 넘던 것")
    faded = tbl[(tbl["피크대비"] <= -50) & (tbl["피크(%)"] >= 5)]
    print(faded.sort_values("피크대비").to_string())

    share.to_csv("data/keyword_share.csv")
    vol.to_csv("data/volume.csv")
    print("\n-> data/keyword_share.csv, data/volume.csv")


if __name__ == "__main__":
    main()
