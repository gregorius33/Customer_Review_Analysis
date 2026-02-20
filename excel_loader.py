"""
엑셀 파일 로드 및 단계적 폴백 열 매핑.
헤더 이름으로 역할(review, rating 등)을 자동 매칭하고, 실패한 항목은 None으로 반환해 GUI에서 선택하게 함.
"""
from __future__ import annotations

import pandas as pd

from config import COLUMN_CANDIDATES


def _normalize(s: str) -> str:
    """공백 제거, 소문자로 통일하여 비교용 문자열 반환."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return "".join(str(s).strip().lower().split())


def load_excel(path: str, sheet_name=0) -> pd.DataFrame:
    """엑셀 파일을 읽어 DataFrame 반환. sheet_name은 시트 인덱스(0이 첫 시트) 또는 시트 이름."""
    return pd.read_excel(path, sheet_name=sheet_name, header=0)


def resolve_columns(df: pd.DataFrame) -> dict[str, str | None]:
    """
    DataFrame의 헤더(컬럼명)를 COLUMN_CANDIDATES와 매칭해 역할별 컬럼명을 반환.
    매칭 실패한 역할은 None.
    반환 예: {"review": "리뷰내용", "rating": "평점", "product": None, ...}
    """
    if df is None or df.empty:
        return {role: None for role in COLUMN_CANDIDATES}

    columns = list(df.columns)
    normalized_columns = {c: _normalize(c) for c in columns}
    result: dict[str, str | None] = {}

    for role, candidates in COLUMN_CANDIDATES.items():
        matched = None
        for cand in candidates:
            n = _normalize(cand)
            for col in columns:
                if normalized_columns[col] == n:
                    matched = col
                    break
            if matched:
                break
        result[role] = matched

    return result


def apply_mapping(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame | None:
    """
    매핑에 따라 필요한 열만 추출한 DataFrame 반환.
    'review' 열은 필수; 없으면 None 반환.
    """
    if df is None or df.empty:
        return None
    review_col = mapping.get("review")
    if not review_col or review_col not in df.columns:
        return None

    cols = [c for c in mapping.values() if c and c in df.columns]
    if not cols:
        return None
    return df[cols].copy()
