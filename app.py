import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

st.set_page_config(page_title="PNPD Sensor Analysis", layout="wide")

st.title("🧪 PNPD 센서 레시피 & 측정 분석 시스템")

# =====================================================
# 1️⃣ Experiment Recipe Used
# =====================================================
st.header("1️⃣ Experiment Recipe Used")

col1, col2, col3 = st.columns(3)

with col1:
    polymer = st.selectbox("Polymer", ["PNPD"])
    polymer_g = st.number_input(
        "Polymer 양 (g)", min_value=0.0, step=0.001, format="%.3f"
    )
    spin_rpm = st.number_input(
        "Spin RPM", min_value=0, step=50
    )

with col2:
    solvent = st.selectbox(
        "Solvent",
        ["EtOH", "Toluene", "IPA", "DMF", "THF"]
    )
    solvent_ml = st.number_input(
        "Solvent 양 (mL)", min_value=0.0, step=0.1, format="%.2f"
    )
    coating_count = st.number_input(
        "Coating 횟수", min_value=1, step=1
    )

with col3:
    cb_type = st.selectbox(
        "CB type",
        ["BP-2000", "XC-72"]
    )
    cb_g = st.number_input(
        "CB 양 (g)", min_value=0.0, step=0.001, format="%.3f"
    )
    electrode_material = st.selectbox(
        "증착 전극",
        ["Ti/Au", "Ag"]
    )

drying = st.selectbox(
    "Drying 조건",
    [
        "24h 상온 건조",
        "100°C 오븐 → 24h 상온 건조",
        "RT 10min → 100°C 10min"
    ]
)

# =====================================================
# 2️⃣ Measurement Result Input
# =====================================================
st.header("2️⃣ Measurement Result Input (kΩ)")

num_electrodes = st.number_input(
    "🔢 전극 개수",
    min_value=1,
    max_value=16,
    step=1,
    value=4
)

baseline_list = []
gas_list = []
bump_list = []

st.subheader("🔧 전극별 저항 입력 (단위: kΩ)")

for i in range(num_electrodes):
    st.markdown(f"⚡ **Electrode {i+1}**")
    c1, c2, c3 = st.columns(3)

    with c1:
        baseline = st.number_input(
            f"E{i+1} Baseline (kΩ)",
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key=f"base_{i}"
        )
    with c2:
        gas = st.number_input(
            f"E{i+1} Gas (kΩ)",
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key=f"gas_{i}"
        )
    with c3:
        bump = st.number_input(
            f"E{i+1} Bump test (kΩ)",
            min_value=0.0,
            step=0.1,
            format="%.2f",
            key=f"bump_{i}"
        )

    baseline_list.append(baseline)
    gas_list.append(gas)
    bump_list.append(bump)

# =====================================================
# ▶ 분석 시작
# =====================================================
if st.button("🔍 분석 시작"):

    df = pd.DataFrame({
        "Baseline (kΩ)": baseline_list,
        "Gas (kΩ)": gas_list,
        "Bump (kΩ)": bump_list
    })

    df["ΔR/R"] = (df["Bump (kΩ)"] - df["Baseline (kΩ)"]) / df["Baseline (kΩ)"]
    df["K-value"] = df["ΔR/R"] / 20000

    st.subheader("📊 계산 결과")
    st.dataframe(df.style.format({
        "Baseline (kΩ)": "{:.2f}",
        "Gas (kΩ)": "{:.2f}",
        "Bump (kΩ)": "{:.2f}",
        "ΔR/R": "{:.4f}",
        "K-value": "{:.6e}"
    }))

    # =================================================
    # 3️⃣ Outlier Detection
    # =================================================
    st.header("3️⃣ 🔎 Outlier Detection")

    if len(df) >= 3:
        iso = IsolationForest(contamination=0.2, random_state=42)
        df["Outlier"] = iso.fit_predict(
            df[["Baseline (kΩ)", "ΔR/R"]]
        )
        df["Outlier"] = df["Outlier"].map({1: "Normal", -1: "Outlier"})
    else:
        df["Outlier"] = "Not checked"

    fig1, ax1 = plt.subplots()
    colors = df["Outlier"].map({
        "Normal": "blue",
        "Outlier": "red",
        "Not checked": "gray"
    })
    ax1.scatter(df["Baseline (kΩ)"], df["ΔR/R"], c=colors)
    ax1.set_xlabel("Baseline (kΩ)")
    ax1.set_ylabel("ΔR/R")
    ax1.set_title("Outlier Detection Result")
    st.pyplot(fig1)

    st.markdown("""
    🔵 **파란색**: 정상 전극  
    🔴 **빨간색**: 이상치 (코팅 불균일, 전극 접촉 문제 가능)
    """)

    # =================================================
    # 4️⃣ Drift Analysis
    # =================================================
    st.header("4️⃣ 📈 Drift Analysis")

    ref = df["Baseline (kΩ)"].iloc[0]
    drift_ratio = (df["Baseline (kΩ)"].mean() - ref) / ref
    drift_detected = abs(drift_ratio) > 0.2

    fig2, ax2 = plt.subplots()
    ax2.plot(df["Baseline (kΩ)"].values, marker="o", label="Baseline")
    ax2.axhline(ref, linestyle="--", color="red", label="Reference")
    ax2.legend()
    ax2.set_title("Baseline Drift Trend")
    st.pyplot(fig2)

    st.markdown(f"""
    📌 Drift 발생 여부: **{drift_detected}**  
    📌 Drift 비율: **{drift_ratio:.2f}**
    """)

    # =================================================
    # 5️⃣ Recommended Recipe
    # =================================================
    st.header("5️⃣ 🧠 추천 레시피 (이유 포함)")

    reco = {
        "Polymer": polymer,
        "Polymer (g)": polymer_g,
        "Solvent": solvent,
        "Solvent (mL)": solvent_ml,
        "CB type": cb_type,
        "CB (g)": cb_g,
        "Spin RPM": spin_rpm,
        "Coating 횟수": coating_count,
        "전극": electrode_material,
        "Drying": drying
    }

    if drift_detected:
        reco["Spin RPM"] += 100
        reco["CB (g)"] = max(0, cb_g - 0.002)
        reco["Coating 횟수"] += 1

    st.table(pd.DataFrame.from_dict(reco, orient="index", columns=["추천 값"]))

    st.markdown("""
    ✅ **추천 이유 (요약)**  
    - Drift 발생 → 막 두께 불균일 가능성  
    - RPM 증가 → 박막 균일도 개선  
    - CB 소폭 감소 → 과도한 percolation 방지  
    - 코팅 횟수 증가 → 전극 간 재현성 향상
    """)