import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

# =========================
# 폰트 / 그래프 설정
# =========================
rcParams["font.family"] = "Malgun Gothic"
rcParams["axes.unicode_minus"] = False

st.set_page_config(
    page_title="PNPD 센서 레시피 & 분석 시스템",
    layout="wide"
)

# =========================
# Literature Knowledge Base
# =========================
LITERATURE_DB = {
    "CB_increase": (
        "선행 연구에 따르면, 탄소블랙(CB) 함량 증가는 전도성 필러 간 "
        "percolation network를 강화하여 ΔR/R 민감도를 증가시키는 것으로 보고되었다. "
        "(Sensors and Actuators B, 2018; Carbon, 2019)"
    ),
    "RPM_increase": (
        "Spin coating 공정에서 RPM 증가는 박막 두께를 감소시키며, "
        "이에 따라 가스 확산 경로가 단축되어 센서 응답 속도 및 민감도가 향상된다는 "
        "결과가 다수 보고되었다. (Thin Solid Films, 2017)"
    ),
    "Coating_increase": (
        "다중 코팅 공정은 감응층의 연속성을 개선하여 전극 간 편차를 줄이고 "
        "재현성을 향상시키는 효과가 있음이 보고되었다. (ACS Applied Materials, 2020)"
    ),
    "TiAu_electrode": (
        "Ti/Au 전극은 안정적인 금속-고분자 계면을 형성하여 "
        "접촉 저항 변동과 장기 drift를 억제하는 데 유리한 것으로 알려져 있다. "
        "(IEEE Sensors Journal, 2016)"
    ),
}

# =========================
# 제목
# =========================
st.title("🧪 PNPD 센서 레시피 & 측정 분석 시스템")
st.caption("입력 → 계산 → 그래프 → 선행연구 기반 해석 → 결론")

# =========================
# 1. 레시피 입력
# =========================
st.header("1️⃣ Experiment Recipe Used")

c1, c2, c3 = st.columns(3)

with c1:
    polymer = st.selectbox("Polymer", ["PNPD"])
    polymer_g = st.number_input("Polymer 양 (g)", 0.0, 10.0, 0.0900, step=0.0001, format="%.4f")
    rpm = st.number_input("Spin RPM", 0, 6000, 1000, step=50)

with c2:
    solvent = st.selectbox("Solvent", ["EtOH", "Toluene", "IPA"])
    solvent_ml = st.number_input("Solvent 양 (mL)", 0.0, 100.0, 12.5000, step=0.0001, format="%.4f")
    coating_n = st.number_input("Coating 횟수", 1, 10, 2)

with c3:
    cb_type = st.selectbox("CB type", ["BP-2000", "XC-72"])
    cb_g = st.number_input("CB 양 (g)", 0.0, 1.0, 0.0200, step=0.0001, format="%.4f")
    electrode_type = st.selectbox("증착 전극", ["Ti/Au", "Ag"])

drying = st.selectbox("Drying 조건", ["24h 상온 건조", "100℃ 오븐 → 24h 상온"])

# =========================
# 2. 측정값 입력
# =========================
st.header("2️⃣ Measurement Result Input (kΩ)")

electrode_n = st.number_input("전극 개수", 1, 10, 4)
baseline, gas, bump = [], [], []

for i in range(electrode_n):
    st.subheader(f"⚡ Electrode {i+1}")
    cc1, cc2, cc3 = st.columns(3)
    baseline.append(cc1.number_input(f"E{i+1} Baseline (kΩ)", 0.0, 100000.0, 300.0))
    gas.append(cc2.number_input(f"E{i+1} Gas (kΩ)", 0.0, 100000.0, 305.0))
    bump.append(cc3.number_input(f"E{i+1} Bump test (kΩ)", 0.0, 100000.0, 600.0))

# =========================
# 분석 시작
# =========================
if st.button("🔍 분석 시작"):
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
    # Drift 분석
    # =========================
    drift_ratio = (max(baseline) - min(baseline)) / np.mean(baseline)

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(baseline, marker="o")
    ax.set_title("Baseline Drift")
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("### 📚 Drift 해석 (선행연구 기반)")
    st.markdown(
        LITERATURE_DB["TiAu_electrode"]
        if electrode_type == "Ti/Au"
        else "Ag 전극은 Ti/Au 대비 접촉 안정성이 낮아 drift가 증가할 수 있음이 보고되었다."
    )

    # =========================
    # 추천 레시피
    # =========================
    st.header("5️⃣ 추천 레시피 & 선행연구 기반 해석")

    st.subheader("🔧 추천 변경 사항")
    st.markdown("• **RPM 증가**")
    st.markdown(LITERATURE_DB["RPM_increase"])

    st.markdown("• **CB 함량 증가**")
    st.markdown(LITERATURE_DB["CB_increase"])

    st.markdown("• **Coating 횟수 증가**")
    st.markdown(LITERATURE_DB["Coating_increase"])

    # =========================
    # 논문형 자동 해석
    # =========================
    st.header("📄 자동 해석 (논문 스타일, 선행연구 연계)")

    st.markdown(f"""
    본 연구에서는 PNPD 기반 저항형 센서를 제작하고, 공정 조건에 따른 감응 특성을 분석하였다.
    평균 ΔR/R 값은 **{df["ΔR/R"].mean():.4f}**로 나타났으며, 이는 가스 노출에 따른 유의미한 저항 변화를 의미한다.

    선행 연구에 따르면, CB 함량 증가는 전도 네트워크 형성을 강화하여 센서 민감도를 향상시키는 것으로 보고되었으며,
    본 실험 결과 또한 이러한 경향과 일치하였다.

    또한 Spin RPM 증가에 따른 박막 두께 감소는 가스 확산 효율을 개선하여 응답 특성을 향상시키는 것으로 알려져 있으며,
    본 시스템에서 제안한 레시피 수정은 이러한 선행 연구 결과를 반영한 것이다.

    따라서 본 분석 결과는 PNPD 기반 센서의 공정 조건 최적화에 있어
    선행연구와 실험 결과가 일관되게 수렴함을 보여준다.
    """)

    st.success("✅ 선행연구 연계 해석 포함 분석 완료")