
import streamlit as st
import json
import random
import re
import pandas as pd
from decimal import Decimal, ROUND_DOWN

# 평균 유량 데이터 로드
with open("학습된_평균유량_데이터.json", "r", encoding="utf-8") as f:
    grouped_flow_map = json.load(f)

# 유해인자 정규화
def normalize_substance(text):
    text = re.sub(r"\([^)]*\)", "", text)  # 괄호 제거
    text = re.sub(r"및|그\s*화합물", "", text)
    text = text.replace(" ", "")
    if "카드뮴" in text:
        return "카드뮴및그화합물"
    return text

# 소수 셋째 자리까지 내림 처리
def trim_to_3_digits(value):
    return float(Decimal(str(value)).quantize(Decimal("0.000"), rounding=ROUND_DOWN))

# 대표 유해인자 추출 (예외 포함)
def extract_representative(substance_str):
    if "규산" in substance_str or "석영" in substance_str:
        return "석영"
    if "산화아연(분진)" in substance_str:
        return "산화아연(분진)"
    if "활석(석면불포함)" in substance_str:
        return "활석(석면불포함)"
    if "활석" in substance_str:
        return "활석"
    if "석탄" in substance_str:
        return "석탄"
    if "산화아연(흄)" in substance_str:
        return "산화아연(흄)"
    if "알루미늄" in substance_str:
        return "알루미늄"
    if "코발트" in substance_str:
        return "코발트"
    if "염화비닐 및 함유물질" in substance_str:
        return "염화비닐"
    if "TDI" in substance_str:
        return "MDI"
    if "메틸렌디페닐디이소시아네이트" in substance_str or (
        "메틸렌디" in substance_str and "디이소시아네이트" in substance_str):
        return "MDI"
    if "안티몬과그화합물" in substance_str:
        return "안티몬"
    if "THF" in substance_str:
        return "테트라하이드로퓨란"
    if "인디움" in substance_str:
        return "인듐"
    if "바륨및그가용성화합물" in substance_str:
        return "바륨"
    if "크롬" in substance_str and "수용성" in substance_str:
        return substance_str

    parts = re.split(r'(?<![0-9A-Za-z]),\s*', substance_str)
    return normalize_substance(parts[0])

# 유량 생성 함수
def generate_flow(rep):
    if rep in ["산화아연(분진)", "활석(석면불포함)", "활석", "석탄"]:
        return 2.201, 2.260
    elif rep == "산화아연(흄)" or ("크롬" in rep and "수용성" in rep):
        return 1.500, 1.585
    elif rep in grouped_flow_map:
        mean = grouped_flow_map[rep]
        if isinstance(mean, list):
            mean = mean[0]
        return round(mean - 0.002, 3), round(mean + 0.002, 3)
    else:
        return None, None

# Streamlit UI
st.title("유량 추천 엔진")

user_input = st.text_area("유해인자 입력 (줄바꿈으로 여러 개)", height=200)

if st.button("유량 추천 실행"):
    substances = [s.strip() for s in user_input.strip().split("\n") if s.strip()]
    results = []

    for substance in substances:
        rep = extract_representative(substance)
        low, high = generate_flow(rep)

        if low is None:
            results.append([substance, rep, "N/A", "N/A"])
        else:
            before = trim_to_3_digits(random.uniform(low, high))
            for _ in range(10):
                after = trim_to_3_digits(random.uniform(low, before))
                if abs(before - after) <= 0.003 and before != after:
                    break
            else:
                after = before
            results.append([substance, rep, before, after])

    # 결과 표 출력
    st.write("### 유량 추천 결과")
    df_result = pd.DataFrame(results, columns=["입력 유해인자", "대표 유해인자", "측정 전 유량", "측정 후 유량"])
    st.dataframe(df_result, use_container_width=True)
