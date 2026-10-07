import streamlit as st
import math
import pandas as pd

# ============================================================
# MINING QUALITY CONTROL & PREDICTION SYSTEM
# CSV-FREE VERSION
# ============================================================
# This version estimates mineral quality directly from four
# process parameters. It does NOT require a CSV or ML model.
#
# Important:
# The target values and weights below are prototype assumptions.
# They should be calibrated with real laboratory/plant data before
# the result is treated as an industrial measurement.
# ============================================================

st.set_page_config(
    page_title="Mining Quality Control & Prediction System",
    page_icon="🏭",
    layout="wide"
)

# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        color: #666;
        margin-bottom: 25px;
    }

    .quality-box {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ddd;
        text-align: center;
    }

    .quality-number {
        font-size: 46px;
        font-weight: 700;
    }

    .small-note {
        color: #666;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# Quality calculation
# ------------------------------------------------------------
def closeness_score(value, optimum, tolerance):
    """
    Returns a score from 0 to 100.

    100 = exactly at the optimum.
    The score decreases smoothly as the value moves away
    from the optimum.
    """
    distance = (value - optimum) / tolerance
    score = 100 * math.exp(-(distance ** 2) / 2)

    return max(0.0, min(100.0, score))


def calculate_quality(ph, slurry, reagent, feed):
    # --------------------------------------------------------
    # Prototype operating targets
    # These are based on the ranges visible in the example
    # dataset supplied during development.
    # --------------------------------------------------------
    targets = {
        "pH": {
            "optimum": 8.0,
            "tolerance": 0.9,
            "weight": 0.30
        },
        "slurry": {
            "optimum": 50.0,
            "tolerance": 12.0,
            "weight": 0.20
        },
        "reagent": {
            "optimum": 18.0,
            "tolerance": 6.0,
            "weight": 0.25
        },
        "feed": {
            "optimum": 220.0,
            "tolerance": 25.0,
            "weight": 0.25
        }
    }

    # Individual parameter scores
    ph_score = closeness_score(
        ph,
        targets["pH"]["optimum"],
        targets["pH"]["tolerance"]
    )

    slurry_score = closeness_score(
        slurry,
        targets["slurry"]["optimum"],
        targets["slurry"]["tolerance"]
    )

    reagent_score = closeness_score(
        reagent,
        targets["reagent"]["optimum"],
        targets["reagent"]["tolerance"]
    )

    feed_score = closeness_score(
        feed,
        targets["feed"]["optimum"],
        targets["feed"]["tolerance"]
    )

    # Weighted overall quality
    quality = (
        ph_score * targets["pH"]["weight"]
        + slurry_score * targets["slurry"]["weight"]
        + reagent_score * targets["reagent"]["weight"]
        + feed_score * targets["feed"]["weight"]
    )

    return (
        max(0.0, min(100.0, quality)),
        ph_score,
        slurry_score,
        reagent_score,
        feed_score
    )


def get_status(quality):
    if quality >= 90:
        return "High Grade", "🟢"
    elif quality >= 75:
        return "Medium Grade", "🟡"
    elif quality >= 60:
        return "Low Grade", "🟠"
    else:
        return "Very Low Grade", "🔴"


def get_recommendations(ph, slurry, reagent, feed):
    recommendations = []

    if ph < 7.5:
        recommendations.append("pH is below the target region. Consider increasing pH.")
    elif ph > 8.5:
        recommendations.append("pH is above the target region. Consider reducing pH.")
    else:
        recommendations.append("pH is close to the target region.")

    if slurry < 40:
        recommendations.append("Slurry intensity is relatively low.")
    elif slurry > 60:
        recommendations.append("Slurry intensity is relatively high.")
    else:
        recommendations.append("Slurry intensity is close to the target region.")

    if reagent < 12:
        recommendations.append("Reagent dose is relatively low.")
    elif reagent > 24:
        recommendations.append("Reagent dose is relatively high.")
    else:
        recommendations.append("Reagent dose is close to the target region.")

    if feed < 195:
        recommendations.append("Feed rate is relatively low.")
    elif feed > 245:
        recommendations.append("Feed rate is relatively high.")
    else:
        recommendations.append("Feed rate is close to the target region.")

    return recommendations


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(
    '<div class="main-title">🏭 Mining Quality Control & Prediction System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Adjust the four process parameters to estimate mineral quality.'
    '</div>',
    unsafe_allow_html=True
)


# ------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------
st.sidebar.header("⚙️ Process Parameters")
st.sidebar.write("Adjust the values and run the quality analysis.")

ph = st.sidebar.slider(
    "Current pH Level",
    min_value=5.0,
    max_value=11.0,
    value=8.0,
    step=0.01
)

slurry = st.sidebar.slider(
    "Slurry Intensity",
    min_value=30.0,
    max_value=70.0,
    value=50.0,
    step=0.1
)

reagent = st.sidebar.slider(
    "Reagent Dose (mL)",
    min_value=5.0,
    max_value=30.0,
    value=18.0,
    step=0.1
)

feed = st.sidebar.slider(
    "Feed Rate (tons/hr)",
    min_value=170.0,
    max_value=270.0,
    value=220.0,
    step=1.0
)


# ------------------------------------------------------------
# Main parameter display
# ------------------------------------------------------------
st.subheader("📡 Current Process Settings")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("pH", f"{ph:.2f}")

with c2:
    st.metric("Slurry Intensity", f"{slurry:.1f}")

with c3:
    st.metric("Reagent Dose", f"{reagent:.1f} mL")

with c4:
    st.metric("Feed Rate", f"{feed:.0f} tons/hr")


st.write("")

run = st.button(
    "🔍 Run Quality Analysis",
    type="primary",
    use_container_width=True
)


# ------------------------------------------------------------
# Analysis
# ------------------------------------------------------------
if run:

    (
        quality,
        ph_score,
        slurry_score,
        reagent_score,
        feed_score
    ) = calculate_quality(
        ph,
        slurry,
        reagent,
        feed
    )

    status, icon = get_status(quality)

    st.divider()

    st.subheader("📊 Diagnostic Report")

    result_col1, result_col2 = st.columns([2, 1])

    with result_col1:
        st.markdown(
            f"""
            <div class="quality-box">
                <div>Estimated Mineral Quality</div>
                <div class="quality-number">{quality:.2f}%</div>
                <div>{icon} {status}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with result_col2:
        st.metric(
            "Overall Quality",
            f"{quality:.2f}%"
        )
        st.write(f"*Grade:* {status}")

    st.write("")

    # --------------------------------------------------------
    # Individual parameter scores
    # --------------------------------------------------------
    st.subheader("📈 Parameter Contribution")

    scores_df = pd.DataFrame({
        "Parameter": [
            "pH",
            "Slurry Intensity",
            "Reagent Dose",
            "Feed Rate"
        ],
        "Current Value": [
            f"{ph:.2f}",
            f"{slurry:.1f}",
            f"{reagent:.1f} mL",
            f"{feed:.0f} tons/hr"
        ],
        "Parameter Score": [
            f"{ph_score:.2f}%",
            f"{slurry_score:.2f}%",
            f"{reagent_score:.2f}%",
            f"{feed_score:.2f}%"
        ],
        "Weight": [
            "30%",
            "20%",
            "25%",
            "25%"
        ]
    })

    st.dataframe(
        scores_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("🎯 Target Operating Values")

    target_df = pd.DataFrame({
        "Parameter": [
            "pH",
            "Slurry Intensity",
            "Reagent Dose",
            "Feed Rate"
        ],
        "Target Value": [
            "8.00",
            "50.0",
            "18.0 mL",
            "220 tons/hr"
        ]
    })

    st.dataframe(
        target_df,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # Progress bars
    # --------------------------------------------------------
    st.subheader("Parameter Scores")

    st.write(f"*pH — {ph_score:.1f}%*")
    st.progress(int(ph_score))

    st.write(f"*Slurry Intensity — {slurry_score:.1f}%*")
    st.progress(int(slurry_score))

    st.write(f"*Reagent Dose — {reagent_score:.1f}%*")
    st.progress(int(reagent_score))

    st.write(f"*Feed Rate — {feed_score:.1f}%*")
    st.progress(int(feed_score))

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------
    st.subheader("💡 Diagnostic Recommendations")

    recommendations = get_recommendations(
        ph,
        slurry,
        reagent,
        feed
    )

    for recommendation in recommendations:
        st.write("• " + recommendation)

    # --------------------------------------------------------
    # Calculation explanation
    # --------------------------------------------------------
    with st.expander("ℹ️ How is the quality calculated?"):
        st.write(
            "Each process parameter receives a score from 0% to 100% "
            "according to how close it is to the selected target operating "
            "value. The four scores are combined using weighted averaging."
        )

        st.latex(
            r"""
            Quality =
            0.30(PH_{score}) +
            0.20(Slurry_{score}) +
            0.25(Reagent_{score}) +
            0.25(Feed_{score})
            """
        )

        st.write(
            "The individual parameter score decreases smoothly as the "
            "parameter moves away from its target."
        )


# ------------------------------------------------------------
# Information section
# ------------------------------------------------------------
st.divider()

with st.expander("📘 About this prototype"):
    st.write(
        "This application is a CSV-free prototype. It does not train a "
        "machine-learning model and does not require historical data. "
        "Instead, it calculates an estimated mineral-quality score from "
        "four configurable process parameters."
    )

    st.warning(
        "The target values, tolerances, and weights are prototype "
        "assumptions. They must be calibrated against laboratory or "
        "industrial measurements before this system can be used for "
        "real operational decision-making."
    )

st.caption(
    "Mining Quality Control & Prediction System • Independent Project • "
    "Prototype / Educational Use"
)