"""
ChatGPT API(gpt-4o-mini)를 사용해 리뷰 데이터 요약·샘플을 전달하고 분석 보고서 텍스트를 생성.
"""
from __future__ import annotations

import os
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from config import (
    DEFAULT_OPENAI_MODEL,
    RATING_NEGATIVE_THRESHOLD,
    RATING_POSITIVE_THRESHOLD,
)

load_dotenv()

# 토큰 제한 고려: 샘플 리뷰 최대 건수 및 한 리뷰당 최대 글자 수
MAX_SAMPLE_REVIEWS = 40
MAX_CHARS_PER_REVIEW = 400


def _get_client(api_key: str | None = None) -> OpenAI | None:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key or not str(key).strip():
        return None
    return OpenAI(api_key=key.strip())


def _build_summary_and_samples(
    df: pd.DataFrame,
    mapping: dict[str, str | None],
) -> str:
    """기본 통계, 평균 평점, 평점별 분포, 긍정/부정/중립 분포, 연령대·성별·구매일자 분포(있으면), 제품별 현황, 리뷰 샘플을 구성."""
    lines = []
    review_col = mapping.get("review")
    if not review_col or review_col not in df.columns:
        return "리뷰 열이 없습니다."

    total = len(df)
    lines.append("=== 기본 통계 ===")
    lines.append(f"총 리뷰 수: {total}")

    product_col = mapping.get("product")
    if product_col and product_col in df.columns:
        n_products = df[product_col].nunique()
        lines.append(f"리뷰된 제품(모델) 수: {n_products}")

    rating_col = mapping.get("rating")
    ratings = pd.Series(dtype=float)
    if rating_col and rating_col in df.columns:
        try:
            ratings = pd.to_numeric(df[rating_col], errors="coerce").dropna()
        except Exception:
            pass

    if len(ratings) > 0:
        lines.append("")
        lines.append("=== 평점 통계 ===")
        lines.append(f"평균 평점: {ratings.mean():.2f}")
        lines.append(f"최소: {ratings.min()}, 최대: {ratings.max()}, 중앙값: {ratings.median():.2f}")
        lines.append("")
        lines.append("평점별 건수 (표 형태):")
        vc = ratings.value_counts().sort_index()
        for score, count in vc.items():
            pct = 100 * count / len(ratings)
            lines.append(f"  평점 {score}: {count}건 ({pct:.1f}%)")
        lines.append("")

        neg = (ratings < RATING_NEGATIVE_THRESHOLD).sum()
        mid = ((ratings >= RATING_NEGATIVE_THRESHOLD) & (ratings < RATING_POSITIVE_THRESHOLD)).sum()
        pos = (ratings >= RATING_POSITIVE_THRESHOLD).sum()
        lines.append("=== 긍정/부정/중립 리뷰 분포 (평점 기준) ===")
        lines.append(f"  부정 (평점 < {RATING_NEGATIVE_THRESHOLD}): {neg}건 ({100*neg/len(ratings):.1f}%)")
        lines.append(f"  중립 (평점 {RATING_NEGATIVE_THRESHOLD}~{RATING_POSITIVE_THRESHOLD} 미만): {mid}건 ({100*mid/len(ratings):.1f}%)")
        lines.append(f"  긍정 (평점 >= {RATING_POSITIVE_THRESHOLD}): {pos}건 ({100*pos/len(ratings):.1f}%)")
        lines.append("")

    age_col = mapping.get("age")
    if age_col and age_col in df.columns:
        try:
            age_vals = df[age_col].astype(str).str.strip()
            age_vals = age_vals[age_vals.str.len() > 0]
            if len(age_vals) > 0:
                lines.append("=== 연령대 분포 ===")
                age_vc = age_vals.value_counts()
                for age, count in age_vc.items():
                    pct = 100 * count / len(age_vals)
                    lines.append(f"  {age}: {count}건 ({pct:.1f}%)")
                lines.append("")
        except Exception:
            pass

    gender_col = mapping.get("gender")
    if gender_col and gender_col in df.columns:
        try:
            gender_vals = df[gender_col].astype(str).str.strip()
            gender_vals = gender_vals[gender_vals.str.len() > 0]
            if len(gender_vals) > 0:
                lines.append("=== 성별 분포 ===")
                gender_vc = gender_vals.value_counts()
                for g, count in gender_vc.items():
                    pct = 100 * count / len(gender_vals)
                    lines.append(f"  {g}: {count}건 ({pct:.1f}%)")
                lines.append("")
        except Exception:
            pass

    purchase_date_col = mapping.get("purchase_date")
    if purchase_date_col and purchase_date_col in df.columns:
        try:
            date_series = pd.to_datetime(df[purchase_date_col], errors="coerce").dropna()
            if len(date_series) > 0:
                lines.append("=== 구매일자 분포 ===")
                lines.append(f"  기간: {date_series.min().strftime('%Y-%m-%d')} ~ {date_series.max().strftime('%Y-%m-%d')}")
                by_month = date_series.dt.to_period("M").value_counts().sort_index()
                for period, count in by_month.items():
                    pct = 100 * count / len(date_series)
                    lines.append(f"  {period}: {count}건 ({pct:.1f}%)")
                lines.append("")
        except Exception:
            pass

    if product_col and product_col in df.columns:
        try:
            top_products = df[product_col].value_counts().head(10)
            lines.append("=== 제품(모델)별 리뷰 수 (상위 10) ===")
            for prod, count in top_products.items():
                lines.append(f"  {prod}: {count}건")
            lines.append("")
        except Exception:
            pass

    reviews_series = df[review_col].astype(str).str.strip()
    reviews_series = reviews_series[reviews_series.str.len() > 0]

    if len(reviews_series) == 0:
        lines.append("=== 리뷰 샘플 ===")
        lines.append("(없음)")
        return "\n".join(lines)

    if rating_col and rating_col in df.columns and len(ratings) > 0:
        try:
            r_numeric = pd.to_numeric(df[rating_col], errors="coerce")
            df_temp = df.assign(__r__=r_numeric).dropna(subset=["__r__"])
            high = df_temp.nlargest(MAX_SAMPLE_REVIEWS // 2, "__r__")
            low = df_temp.nsmallest(MAX_SAMPLE_REVIEWS // 2, "__r__")
            indices = high.index.tolist() + low.index.tolist()
            indices = list(dict.fromkeys(indices))[:MAX_SAMPLE_REVIEWS]
        except Exception:
            indices = reviews_series.index[:MAX_SAMPLE_REVIEWS].tolist()
    else:
        indices = reviews_series.index[:MAX_SAMPLE_REVIEWS].tolist()

    lines.append("=== 리뷰 텍스트 샘플 (상·하위 평점 위주) ===")
    for i, idx in enumerate(indices, 1):
        text = reviews_series.loc[idx]
        if len(text) > MAX_CHARS_PER_REVIEW:
            text = text[:MAX_CHARS_PER_REVIEW] + "..."
        lines.append(f"[{i}] {text}")
    return "\n".join(lines)


def generate_report(
    df: pd.DataFrame,
    mapping: dict[str, str | None],
    api_key: str | None = None,
    model: str | None = None,
) -> tuple[str, str | None]:
    """
    리뷰 DataFrame과 열 매핑을 받아 ChatGPT로 분석 보고서를 생성.
    반환: (보고서_문자열, 에러메시지).
    성공 시 에러메시지는 None.
    """
    client = _get_client(api_key)
    if not client:
        return "", "API 키가 없습니다. .env 파일에 OPENAI_API_KEY를 설정하세요."

    model = model or DEFAULT_OPENAI_MODEL
    data_text = _build_summary_and_samples(df, mapping)

    system = (
        "당신은 고객 리뷰 데이터를 분석하는 전문가입니다. "
        "주어진 통계와 리뷰 샘플을 바탕으로 **반드시 마크다운(Markdown) 문법만 사용**한 한국어 분석 보고서를 작성합니다. "
        "출력 전체가 .md 파일로 저장될 수 있도록, 아래 문법을 정확히 사용하세요.\n\n"
        "【마크다운 문법 필수】\n"
        "- 제목: 첫 줄에 # 제목 (H1)\n"
        "- 섹션 제목: ## 섹션명, ### 소섹션명\n"
        "- 표: 반드시 헤더 행 + 구분선 + 데이터 행. 예시:\n"
        "  | 항목 | 값 |\n"
        "  |---|---|\n"
        "  | 총 리뷰 수 | 100건 |\n"
        "- 목록: 하이픈 - 또는 별표 * 또는 숫자 1. 2.\n"
        "- 강조: **굵게**\n\n"
        "【필수 구성】\n"
        "1. # 제목 (H1 한 개)\n"
        "2. ## 요약 + 2~4문단\n"
        "3. ## 기본 통계 + 마크다운 표\n"
        "4. ## 평균 평점 및 평점별 분포 + 표\n"
        "5. ## 긍정/부정/중립 리뷰 분포 + 표\n"
        "6. ## 연령대 분포 + 표 (데이터 있을 때만)\n"
        "7. ## 성별 분포 + 표 (데이터 있을 때만)\n"
        "8. ## 구매일자 분포 + 표 (데이터 있을 때만)\n"
        "9. ## 제품별 현황 + 표 또는 목록\n"
        "10. ## 상세 분석 + - 목록\n"
        "11. ## 개선점 및 제안 + - 목록\n\n"
        "일반 텍스트만 나열하지 말고, 모든 섹션에 ## 제목과 표(|) 또는 목록(-)을 반드시 사용하세요."
    )
    user = (
        "다음은 노트북 구매 고객 리뷰 데이터의 통계와 샘플입니다.\n\n"
        f"{data_text}\n\n"
        "위 데이터를 바탕으로 **마크다운 문법만 사용**한 분석 보고서를 작성해 주세요. "
        "제목은 #, 섹션은 ##, 표는 | 열 | 열 | 와 다음 줄 |---|---| 형식, 목록은 - 로 작성하세요. "
        "저장 시 .md 파일에서 표와 제목이 제대로 렌더링되도록 반드시 마크다운 문법을 사용하세요."
    )

    try:
        response: Any = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        report = (response.choices[0].message.content or "").strip()
        return report, None
    except Exception as e:
        return "", str(e)
