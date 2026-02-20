---
name: 리뷰 분석 GUI + ChatGPT 보고서
overview: 엑셀 파일 선택 → 단계적 폴백으로 리뷰/평점 등 열 매핑 → ChatGPT API로 분석 보고서 생성까지를 GUI로 수행하는 프로그램을 구성합니다. API 키는 .env에 저장합니다.
todos: []
isProject: false
---

# 고객 리뷰 분석 GUI 프로그램 구현 계획

## 목표

- **GUI**: 파일 선택, 열 매핑(자동 감지 실패 시 사용자 선택), 분석 실행, 보고서 표시/저장
- **단계적 폴백**: 헤더 이름 매칭 → 매칭 실패 시 화면에서 열 선택
- **보고서 생성**: 리뷰 데이터 요약·통계를 ChatGPT API에 전달해 **마크다운(.md)** 형식 분석 보고서 생성
- **API 키**: `.env` 파일에 저장, 사용자가 직접 입력
- **처리 중 표시**: 분석 실행 시 "생성 중..." 버튼·상태 메시지로 진행 상태 안내

---

## 기술 스택

| 용도 | 선택 |
|------|------|
| GUI | **Tkinter** (Python 기본 내장, 추가 설치 없음) |
| 엑셀 읽기 | pandas + openpyxl |
| 환경 변수 | python-dotenv |
| ChatGPT API | openai (OpenAI 공식 패키지, ChatGPT API 호출) |

---

## 프로젝트 구조

```
24.Customer_Review_Analysis/
├── .env                    # OPENAI_API_KEY=sk-... (사용자 작성, .gitignore 권장)
├── .env.example            # OPENAI_API_KEY= 항목만 있는 샘플
├── requirements.txt        # pandas, openpyxl, python-dotenv, openai
├── main.py                 # GUI 진입점
├── excel_loader.py         # 엑셀 로드 + 단계적 폴백 열 매핑
├── report_generator.py     # ChatGPT API 호출 및 보고서 생성
└── (선택) config.py        # 열 이름 후보 목록 등 상수
```

---

## 1. .env 및 API 키

- **.env** (프로젝트 루트): `OPENAI_API_KEY=sk-...` 한 줄. 사용자가 직접 입력.
- **.env.example**: `OPENAI_API_KEY=` 만 적어 두어 항목 이름 안내.
- **로드**: `python-dotenv`로 `load_dotenv()` 후 `os.getenv("OPENAI_API_KEY")`. API 호출 전에 키 없으면 GUI에서 경고 메시지 표시.

---

## 2. 엑셀 로드 및 단계적 폴백 (excel_loader.py)

- **역할별 헤더 후보** (config.py): review, rating, product, customer_id, name, **age**, **purchase_date**, **gender**
- **동작**: `load_excel(path)`, `resolve_columns(df)` → 역할별 컬럼명 또는 None. GUI에서 None인 역할은 드롭다운으로 선택.
- **config.py**: `RATING_POSITIVE_THRESHOLD`, `RATING_NEGATIVE_THRESHOLD` 로 긍정/부정 구분.

---

## 3. ChatGPT 보고서 생성 (report_generator.py)

### 사용 모델 (가성비 추천)

- **기본 추천: `gpt-4o-mini`** — 리뷰 요약·보고서에 충분, 입력/출력 단가 저렴.

### 전달 통계 및 보고서 형식

- **전달 데이터**: 기본 통계(총 리뷰 수, 제품 수), 평균 평점·평점별 분포, 긍정/부정/중립 리뷰 분포(평점 기준), 연령대·성별·구매일자 분포(열 매핑된 경우), 제품별 리뷰 수, 리뷰 텍스트 샘플.
- **출력 형식**: **마크다운(.md)**. 프롬프트에서 `#` 제목, `##` 섹션, `| 표 |` 구문, `-` 목록 사용을 명시해 .md 저장 시 렌더링되도록 함.
- 에러 처리: 키 없음, 네트워크 오류, rate limit 등 사용자 메시지 반환.

---

## 4. GUI (main.py)

- 파일 선택 → 로드 → 매핑 표시/콤보박스 선택(연령, 구매일자, 성별 포함) → 분석 실행 → 보고서 표시 / 저장.
- **분석 실행 시**: 버튼 문구 "생성 중...", 상태 라벨 "분석 보고서 생성 중... 잠시만 기다려 주세요." 표시 → 완료 시 "생성 완료."
- **저장**: 기본 확장자 `.md`, 파일 유형 마크다운 우선.

---

## 5. requirements.txt

pandas, openpyxl, python-dotenv, openai

---

## 6. .gitignore

.env 추가.
