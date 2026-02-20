# 열(컬럼) 역할별 헤더 후보 목록 (대소문자/공백 무시 매칭)
COLUMN_CANDIDATES = {
    "review": [
        "리뷰내용", "리뷰 내용", "Review", "review_content", "리뷰",
        "review content", "내용", "코멘트", "comment",
    ],
    "rating": [
        "평점", "점수", "rating", "Rating", "별점", "점", "score", "Score",
    ],
    "product": [
        "구매한 노트북 모델", "노트북 모델", "모델", "product", "제품명",
        "제품", "상품", "노트북", "model", "Model",
    ],
    "customer_id": [
        "고객ID", "고객 id", "customer_id", "ID", "id", "고객코드", "코드",
    ],
    "name": [
        "이름", "name", "Name", "고객명", "구매자", "작성자",
    ],
    "age": [
        "연령", "연령대", "age", "Age", "나이", "연령구간",
    ],
    "purchase_date": [
        "구매일자", "구매일", "구매 날짜", "purchase_date", "date", "Date",
        "날짜", "작성일", "리뷰일", "order_date", "created_at",
    ],
    "gender": [
        "성별", "gender", "Gender", "남녀", "sex", "Sex",
    ],
}

# 긍정/부정 구분용 평점 기준 (이하면 부정, 이상이면 긍정, 그 사이는 중립)
RATING_POSITIVE_THRESHOLD = 4.0  # 이 점수 이상 = 긍정
RATING_NEGATIVE_THRESHOLD = 2.5  # 이 미만 = 부정, 이상 = 중립 또는 긍정

# 분석 보고서 생성에 사용할 기본 모델
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
