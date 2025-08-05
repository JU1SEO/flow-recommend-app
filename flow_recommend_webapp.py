import streamlit as st
import pandas as pd
import json
import random
import re

# ---------------------------
# 데이터 불러오기 함수
# ---------------------------
@st.cache_data
def load_flow_data():
    with open("학습된_평균유량_데이터.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 실제 데이터 로딩
data = load_flow_data()

# 유량 추천 중복 방지를 위한 기록 저장용 집합
used_flows = set()

# ---------------------------
# 대표 유해인자 추출 함수
# 괄호 포함 원본으로 매핑 우선 체크
# ---------------------------
def extract_representative(substance_str):
    original = substance_str  # 원본 보존

    # 괄호 포함 원본 기준으로 특정 문자열 우선 매핑
    if "산화아연(분진)" in original:
        representative = "텅스텐"
    elif "산화아연(흄)" in original:
        representative = "아연"
    else:
        # 괄호 제거, 기타 문구 제거, 공백 제거
        substance_str = re.sub(r"\([^)]*\)", "", substance_str)  # 괄호 제거
        substance_str = re.sub(r"및|그\s*화합물", "", substance_str)
        substance_str = substance_str.replace(" ", "")

        # 화학식 쉼표 보호 처리 (예: 1,1- → 1§1-, N,N- → N§N-)
        protected = substance_str
        protected = re.sub(r'(\d),(\d-)', r'\1§\2', protected)
        protected = re.sub(r'N,N-', 'N§N-', protected)

        # 쉼표 기준 첫 항목 추출, 보호 문자 원복
        parts = protected.split(",")
        representative = parts[0].replace("§", ",")

        # 기타 매핑 규칙 적용
        if "납" in representative:
            representative = "납"
        elif "산화규소" in representative or "규산" in representative:
            representative = "석영"
        elif "카드뮴" in representative:
            representative = "카드뮴및그화합물"
        elif "메틸렌디페닐디이소시아네이트" in representative:
            representative = "MDI"
        elif "인디움" in representative:
            representative = "인듐"
        elif "바륨" in representative:
            representative = "바륨"
        elif "크롬" in representative:
            representative = "크롬"
        elif "활석" in representative or "석탄" in representative:
            representative = "텅스텐"
        elif "안티몬" in representative:
            representative = "삼산화안티몬"
        elif "염화비닐" in representative:
            representative = "염화비닐"
        elif "코발트" in representative:
            representative = "코발트"

    return representative

# ---------------------------
# 유량 추천 함수
# ---------------------------
def recommend_flow(rep):
    # 해당 대표 유해인자가 데이터에 없으면 결과 없음 반환
    if rep not in data:
        return "N/A", "N/A"

    # 중복 추천 방지: 기존에 추천된 유량은 제외하고 선택
    flows = data[rep]
    candidates = [f for f in flows if f not in used_flows]

    # 모든 유량이 사용된 경우, 중복 허용
    if not candidates:
        candidates = flows

    # 랜덤 선택
    base = float(random.choice(candidates))
    used_flows.add(base)

    # 0.001 ~ 0.003 범위 내 무작위 편차
    delta = round(random.uniform(0.001, 0.003), 3)

    # 편차를 이용해 측정 전/후 유량 생성
    before = round(base + delta / 2, 3)
    after = round(before - delta, 3)

    # 측정 전/후 유량이 같으면 0.001 더해줌
    if before == after:
        before = round(before + 0.001, 3)

    # 소수 셋째 자리까지 문자열로 반환
    return f"{before:.3f}", f"{after:.3f}"

# ---------------------------
# Streamlit UI
# ---------------------------

# 앱 제목
st.title("유해인자 유량 추천 엔진")

# 하단 고정 텍스트 (개발자 정보)
st.markdown(
    """
    <style>
    .custom-footer-left {
        position: fixed;
        bottom: 10px;
        left: 10px;
        font-size: 11px;
        color: white;
        opacity: 0.6;
        user-select: none;
        z-index: 9999;
        font-family: Arial, sans-serif;
    }
    </style>
    <div class="custom-footer-left">developed by. 서주원</div>
    """,
    unsafe_allow_html=True,
)

# 세션 상태에 입력값 초기화용 키 생성
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# 입력창과 버튼 두 개를 한 줄에 배치하기 위해 컬럼 분리
col1, col2 = st.columns([4, 1])

with col1:
    # 유해인자 입력창
    user_input = st.text_area(
        "유해인자명을 입력하세요",
        value=st.session_state.user_input,
        key="user_input",
        height=250,
        placeholder="""\
각 줄에 한 개씩 유해인자명을 입력하세요.
복수 유해인자는 쉼표로 구분 가능합니다.

예시:
1. 용접흄
2. 산화철분진과흄, 망간, 이산화티타늄, 3가크롬, 니켈(불용성)
3. 6가크롬
4. 헥산, 초산에틸, 아세톤, 테트라하이드로퓨란
"""
    )

with col2:
    # 유량 추천 실행 버튼
    if st.button("유량 추천 실행"):
        # 입력값이 비어있지 않으면 실행
        if st.session_state.user_input.strip() != "":
            rows = []
            substances = [x.strip() for x in st.session_state.user_input.split("\n") if x.strip()]
            for line in substances:
                rep = extract_representative(line)
                before, after = recommend_flow(rep)
                rows.append((line, rep, before, after))

            result_df = pd.DataFrame(rows, columns=["입력 유해인자", "대표 유해인자", "측정 전 유량", "측정 후 유량"])
            # 결과 테이블 출력 (높이 800px)
            st.dataframe(result_df, use_container_width=True, height=800)

            # CSV 다운로드 버튼
            st.download_button("결과 다운로드 (CSV)", result_df.to_csv(index=False).encode("utf-8-sig"), file_name="유량추천결과.csv")

    # 입력창 초기화 버튼
    if st.button("입력창 초기화"):
        st.session_state.user_input = ""
