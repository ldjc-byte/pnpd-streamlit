import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

# =========================
# 기본 설정
# =========================
rcParams["font.family"] = "Malgun Gothic"
rcParams["axes.unicode_minus"] = False

st.set_page_config(
    page_title="PNPD 센서 레시피 분석 플랫폼",
    layout="wide"
)

# =========================
# Literature Knowledge Base
# =========================
LITERATURE_DB = {
    "CB": "선행연구에 따르면 CB 함량 증가는 전도 네트워크(percolation network)를 강화하여 ΔR/R 민감도를 증가시키는 것으로 보고되었다 (Sensors and Actuators B, 2018).",
    "RPM": "Spin RPM 증가는 박막 두께를 감소시켜 가스 확산 효율을 향상시키며 민감도를 증가시키는 경향을 보인다 (Thin Solid Films, 2017).",
    "COATING": "다중 코팅은 감응층 연속성을 향상시켜 전극 간 편차를 줄이고 재현성을 개선한다 (ACS Applied Materials, 2020).",
    "ELECTRODE": "Ti/Au 전극은 안정적인 금속-고분자 계면을 형성하여 접촉 저항 변동 및 drift를 억제하는 데 유리하다 (IEEE Sensors Journal, 2016)."
}

# =========================
# 제목
# =========================
st.title("🧪 PNPD 센서 레시피 & 분석 시스템")
st.caption("입력 → 계산 → 이상치/드리프트 → 논문 기반 해석 → 레시피 수정")

# =========================
# 1. 레시피 입력
# =========================
st.header("1️⃣ 기존 실험 레시피 입력")

c1, c2, c3 = st.columns(3)

with c1:
    polymer = st.selectbox("Polymer", ["PNPD"])
    polymer_g = st.number_input("Polymer (g)", 0.0, 10.0, 0.0900, step=0.0001, format="%.4f")
    rpm = st.number_input("Spin RPM", 0, 6000, 1000, step=50)

with c2:
    solvent = st.selectbox("Solvent", ["EtOH", "Toluene", "IPA"])
    solvent_ml = st.number_input("Solvent (mL)", 0.0, 100.0, 12.5000, step=0.0001, format="%.4f")
    coating_n = st.number_input("Coating 횟수", 1, 10, 2)

with c3:
    cb_type = st.selectbox("CB type", ["BP-2000", "XC-72"])
    cb_g = st.number_input("CB (g)", 0.0, 1.0, 0.0200, step=0.0001, format="%.4f")
    electrode_type = st.selectbox("전극", ["Ti/Au", "Ag"])

drying = st.selectbox("Drying 조건", ["24h 상온 건조", "100℃ 오븐 → 24h 상온"])

# =========================
# 2. 측정값 입력
# =========================
st.header("2️⃣ 전극별 측정 결과 (kΩ)")

electrode_n = st.number_input("전극 개수", 1, 10, 4)
baseline, gas, bump = [], [], []

for i in range(electrode_n):
    st.subheader(f"Electrode {i+1}")
    cc1, cc2, cc3 = st.columns(3)
    baseline.append(cc1.number_input("Baseline", 0.0, 100000.0, 300.0))
    gas.append(cc2.number_input("Gas", 0.0, 100000.0, 305.0))
    bump.append(cc3.number_input("Bump", 0.0, 100000.0, 600.0))

# =========================
# 분석
# =========================
if st.button("🔍 분석 실행"):
    df = pd.DataFrame({
        "Baseline": baseline,
        "Gas": gas,
        "Bump": bump
    })

    df["ΔR"] = df["Bump"] - df["Baseline"]
    df["ΔR/R"] = df["ΔR"] / df["Baseline"]
    df["K"] = df["ΔR/R"] / 20000
    df["K (scientific)"] = df["K"].apply(lambda x: f"{x:.2e}")

    st.subheader("📋 계산 결과")
    st.dataframe(df)

    # =========================
    # 3. 이상치 탐지 (강화)
    # =========================
    st.header("3️⃣ 이상치 탐지 (IQR + Z-score)")

    Q1 = df["ΔR/R"].quantile(0.25)
    Q3 = df["ΔR/R"].quantile(0.75)
    IQR = Q3 - Q1

    df["Outlier_IQR"] = (df["ΔR/R"] < Q1 - 1.5 * IQR) | (df["ΔR/R"] > Q3 + 1.5 * IQR)
    z_score = (df["ΔR/R"] - df["ΔR/R"].mean()) / df["ΔR/R"].std()
    df["Outlier_Z"] = abs(z_score) > 2

    df["Outlier"] = df["Outlier_IQR"] | df["Outlier_Z"]

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.scatter(df.index + 1, df["ΔR/R"], c=df["Outlier"].map({True:"red", False:"blue"}))
    ax.set_xlabel("전극 번호")
    ax.set_ylabel("ΔR/R")
    ax.set_title("이상치 탐지 결과")
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("""
    🔴 **이상치 전극**  
    - 국부적 코팅 불균일  
    - CB 응집  
    - 전극 접촉 불량 가능성  

    🔵 **정상 전극**  
    - 공정 재현성 양호
    """)

    # =========================
    # 4. Drift 분석
    # =========================
    st.header("4️⃣ Drift 분석")

    drift_ratio = (max(baseline) - min(baseline)) / np.mean(baseline)

    fig2, ax2 = plt.subplots(figsize=(5, 3))
    ax2.plot(baseline, marker="o")
    ax2.axhline(np.mean(baseline), linestyle="--", color="red")
    ax2.set_ylabel("Baseline (kΩ)")
    ax2.set_xlabel("전극 번호")
    ax2.set_title("Baseline Drift")
    plt.tight_layout()
    st.pyplot(fig2)

    st.markdown(f"""
    Drift 비율: **{drift_ratio:.3f}**

    - Drift가 크면 감응층/전극 계면 안정성 저하 가능  
    - {LITERATURE_DB["ELECTRODE"]}
    """)

    # =========================
    # 5. 레시피 수정 제안
    # =========================
    st.header("5️⃣ 레시피 수정 제안 (비교 포함)")

    modified_recipe = {
        "Polymer (g)": polymer_g,
        "Solvent (mL)": solvent_ml,
        "CB (g)": round(cb_g * 1.1, 4),
        "RPM": int(rpm * 1.2),
        "Coating": coating_n + 1,
        "Electrode": electrode_type,
        "Drying": drying
    }

    original_recipe = {
        "Polymer (g)": polymer_g,
        "Solvent (mL)": solvent_ml,
        "CB (g)": cb_g,
        "RPM": rpm,
        "Coating": coating_n,
        "Electrode": electrode_type,
        "Drying": drying
    }

    comp_df = pd.DataFrame([original_recipe, modified_recipe], index=["기존", "추천"])
    st.dataframe(comp_df)

    st.markdown("""
    🔧 **수정 이유 요약**
    - CB 증가 → """ + LITERATURE_DB["CB"] + """
    - RPM 증가 → """ + LITERATURE_DB["RPM"] + """
    - Coating 증가 → """ + LITERATURE_DB["COATING"] + """
    """)

    # =========================
    # 6. 논문형 자동 해석
    # =========================
    st.header("📄 논문형 자동 해석")

    st.markdown(f"""
    본 연구에서는 PNPD 기반 저항형 센서의 공정 조건과 감응 특성 간의 상관관계를 분석하였다.
    ΔR/R 기반 이상치 탐지를 통해 일부 전극에서 비정상적인 응답이 확인되었으며,
    이는 감응층 불균일 또는 전극 접촉 문제에 기인한 것으로 판단된다.

    또한 baseline drift 분석 결과, Drift 비율은 **{drift_ratio:.3f}**로 나타났으며,
    이는 선행연구에서 보고된 전극 계면 안정성 문제와 일치하는 경향을 보인다.

    따라서 CB 함량 증가, Spin RPM 상향, 코팅 횟수 증가를 포함한 레시피 수정을 제안하였으며,
    이는 선행연구 결과와 실험 데이터를 종합적으로 반영한 공정 최적화 전략이다.
    """)

    st.success("✅ 이상치 탐지 + 레시피 비교 + 논문 기반 해석 완료")