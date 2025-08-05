import streamlit as st
import pandas as pd
import json
import random
import re

# ---------------------------
# 데이터 불러오기
# ---------------------------
@st.cache_data
def load_flow_data():
    with open("학습된_평균유량_데이터.json", "r", encoding="utf-8") as f:
        return json.load(f)

data = load_flow_data()
used_flows = set()

# ---------------------------
# 대표 유해인자 추출 함수 (괄호 포함 원본으로 매핑 우선 체크)
# ---------------------------
def extract_representative(substance_str):
    original = substance_str  # 원본 보존

    # 매핑 조건은 원본 기준 검사 (괄호 포함 상태)
    if "산화아연(분진)" in original:
        representative = "텅스텐"
    elif "산화아연(흄)" in original:
        representative = "아연"
    else:
        # 괄호 제거 등 기존 정제
        substance_str = re.sub(r"\([^)]*\)", "", substance_str)  # 괄호 제거
        substance_str = re.sub(r"및|그\s*화합물", "", substance_str)
        substance_str = substance_str.replace(" ", "")

        # 화학식 패턴 보호: 1,1- → 1§1-, N,N- → N§N-
        protected = substance_str
        protected = re.sub(r'(\d),(\d-)', r'\1§\2', protected)
        protected = re.sub(r'N,N-', 'N§N-', protected)

        parts = protected.split(",")
        representative = parts[0].replace("§", ",")

        # 기타 매핑 규칙
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
    if rep not in data:
        return "N/A", "N/A"

    # 추천 유량 선택 (중복 방지)
    flows = data[rep]
    candidates = [f for f in flows if f not in used_flows]
    if not candidates:
        candidates = flows  # 모두 사용되었으면 초기화
    base = float(random.choice(candidates))
    used_flows.add(base)

    delta = round(random.uniform(0.001, 0.003), 3)
    before = round(base + delta / 2, 3)
    after = round(before - delta, 3)

    if before == after:
        before = round(before + 0.001, 3)

    return f"{before:.3f}", f"{after:.3f}"

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("유량 추천 엔진")

user_input = st.text_area("유해인자명을 입력하세요 (쉼표로 구분)", height=150)

if st.button("유량 추천 실행") and user_input:
    rows = []
    substances = [x.strip() for x in user_input.split("\n") if x.strip()]
    for line in substances:
        rep = extract_representative(line)
        before, after = recommend_flow(rep)
        rows.append((line, rep, before, after))

    result_df = pd.DataFrame(rows, columns=["입력 유해인자", "대표 유해인자", "측정 전 유량", "측정 후 유량"])
    st.dataframe(result_df, use_container_width=True)

    st.download_button("결과 다운로드 (CSV)", result_df.to_csv(index=False).encode("utf-8-sig"), file_name="유량추천결과.csv")
