import streamlit as st
import pandas as pd
import random
import re
import json

# 데이터 로딩
@st.cache_data
def load_data():
    flow_data = pd.read_excel("정제된_추천유량학습데이터.xlsx")
    with open("학습된_평균유량_데이터.json", "r", encoding="utf-8") as f:
        grouped_flow_map = json.load(f)
    return flow_data, grouped_flow_map

flow_data, grouped_flow_map = load_data()

# 정규화 함수 (카드뮴 보완 포함)
def normalize_substance(text):
    text = re.sub(r"\([^)]*\)", "", text)  # 괄호 제거
    text = re.sub(r"및|그\s*화합물", "", text)
    text = text.replace(" ", "")
    if "카드뮴" in text:
        return "카드뮴및그화합물"
    return text

# 대표 유해인자 추출 (쉼표는 첫 항목 기준, 화학식 쉼표 유지)
def extract_representative(substance_str):
    parts = re.split(r'(?<![A-Za-z]),\s*', substance_str)
    return normalize_substance(parts[0])

# 유량 생성 함수
def generate_flow(base_flow):
    delta = round(random.uniform(0.001, 0.003), 3)
    flow_before = round(base_flow + delta / 2, 3)
    flow_after = round(flow_before - delta, 3)
    if flow_before == flow_after:
        flow_before = round(flow_before + 0.001, 3)
    return flow_before, flow_after

# Streamlit UI
st.title("유량 추천 엔진 (웹 앱)")

input_text = st.text_area("유해인자 입력 (쉼표로 구분된 여러 항목 가능)", "카드뮴, 아세톤, 메틸알코올")

if st.button("유량 추천 실행"):
    input_lines = input_text.strip().split("\n")
    results = []
    used_flows = {}

    for line in input_lines:
        rep = extract_representative(line)
        if rep not in grouped_flow_map:
            results.append((line, rep, "N/A", "N/A"))
            continue

        base_flow = float(random.choice(grouped_flow_map[rep]))
        for _ in range(10):
            before, after = generate_flow(base_flow)
            if used_flows.get(rep) != (before, after):
                break
        used_flows[rep] = (before, after)

        results.append((line, rep, f"{before:.3f}", f"{after:.3f}"))

    result_df = pd.DataFrame(results, columns=["입력 유해인자", "대표 유해인자", "측정 전 유량", "측정 후 유량"])
    st.dataframe(result_df, use_container_width=True)