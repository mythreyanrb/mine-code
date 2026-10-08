# ============================================================
# MINERAL QUALITY & FEASIBILITY ANALYZER
# STREAMLIT VERSION
# ============================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Mineral Quality & Feasibility Analyzer",
    page_icon="⛏️",
    layout="wide"
)


# ============================================================
# 2. CUSTOM HEADER
# ============================================================

st.title("⛏️ Mineral Quality & Feasibility Analyzer")

st.markdown(
    """
    **Mineral quality screening, chemical assessment, physical
    characteristics and economic feasibility analysis**
    """
)

st.divider()


# ============================================================
# 3. MINERAL INFORMATION
# ============================================================

st.header("1. Mineral / Ore Information")

col1, col2 = st.columns(2)

with col1:
    mineral_name = st.text_input(
        "Mineral / Ore Name",
        value="Iron Ore"
    )

with col2:
    sample_id = st.text_input(
        "Sample ID",
        value="SAMPLE-001"
    )


# ============================================================
# 4. CHEMICAL COMPOSITION
# ============================================================

st.header("2. Chemical Composition")

col1, col2, col3 = st.columns(3)

with col1:
    main_component = st.text_input(
        "Main Valuable Component",
        value="Fe"
    )

with col2:
    main_component_percent = st.number_input(
        "Main Component (%)",
        min_value=0.0,
        max_value=100.0,
        value=60.0,
        step=0.1
    )

with col3:
    impurity_percent = st.number_input(
        "Total Impurities (%)",
        min_value=0.0,
        max_value=100.0,
        value=10.0,
        step=0.1
    )


# ============================================================
# 5. PH
# ============================================================

st.header("3. pH Analysis")

ph = st.number_input(
    "pH of Ore / Sample",
    min_value=0.0,
    max_value=14.0,
    value=7.0,
    step=0.1
)


# ============================================================
# 6. CHEMICAL STABILITY
# ============================================================

st.header("4. Chemical Stability")

stability = st.slider(
    "Chemical Stability Rating",
    min_value=1,
    max_value=5,
    value=3,
    help=(
        "1 = Highly unstable | "
        "2 = Unstable | "
        "3 = Moderately stable | "
        "4 = Stable | "
        "5 = Highly stable"
    )
)

st.caption(
    "1 = Highly unstable | 2 = Unstable | "
    "3 = Moderately stable | 4 = Stable | "
    "5 = Highly stable"
)


# ============================================================
# 7. REACTIVITY
# ============================================================

st.header("5. Chemical Reactivity")

reactivity = st.slider(
    "Reactivity Rating",
    min_value=1,
    max_value=5,
    value=3,
    help=(
        "1 = Highly reactive | "
        "2 = Reactive | "
        "3 = Moderately reactive | "
        "4 = Low reactivity | "
        "5 = Very low reactivity"
    )
)

st.caption(
    "1 = Highly reactive | 2 = Reactive | "
    "3 = Moderately reactive | 4 = Low reactivity | "
    "5 = Very low reactivity"
)


# ============================================================
# 8. PHYSICAL CHARACTERISTICS
# ============================================================

st.header("6. Physical Characteristics")

col1, col2, col3 = st.columns(3)

with col1:
    particle_size = st.number_input(
        "Average Particle Size (mm)",
        min_value=0.0,
        value=1.0,
        step=0.1
    )

with col2:
    density = st.number_input(
        "Bulk Density (g/cm³)",
        min_value=0.0,
        value=2.5,
        step=0.1
    )

with col3:
    hardness = st.number_input(
        "Hardness (Mohs)",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.1
    )


# ============================================================
# 9. MOISTURE & HOMOGENEITY
# ============================================================

st.header("7. Moisture & Homogeneity")

col1, col2 = st.columns(2)

with col1:
    moisture = st.number_input(
        "Moisture Content (%)",
        min_value=0.0,
        max_value=100.0,
        value=5.0,
        step=0.1
    )

with col2:
    homogeneity = st.slider(
        "Homogeneity Rating",
        min_value=1,
        max_value=5,
        value=3,
        help=(
            "1 = Highly heterogeneous | "
            "2 = Heterogeneous | "
            "3 = Moderately homogeneous | "
            "4 = Homogeneous | "
            "5 = Highly homogeneous"
        )
    )

st.caption(
    "1 = Highly heterogeneous | 2 = Heterogeneous | "
    "3 = Moderately homogeneous | 4 = Homogeneous | "
    "5 = Highly homogeneous"
)


# ============================================================
# 10. ECONOMIC FEASIBILITY
# ============================================================

st.header("8. Economic Feasibility")

col1, col2 = st.columns(2)

with col1:
    market_price = st.number_input(
        "Expected Selling Price per Tonne",
        min_value=0.0,
        value=10000.0,
        step=100.0
    )

    mining_cost = st.number_input(
        "Mining Cost per Tonne",
        min_value=0.0,
        value=2500.0,
        step=100.0
    )

    processing_cost = st.number_input(
        "Processing Cost per Tonne",
        min_value=0.0,
        value=2000.0,
        step=100.0
    )

with col2:
    transport_cost = st.number_input(
        "Transportation Cost per Tonne",
        min_value=0.0,
        value=1000.0,
        step=100.0
    )

    other_cost = st.number_input(
        "Other Cost per Tonne",
        min_value=0.0,
        value=500.0,
        step=100.0
    )


# ============================================================
# 11. CALCULATION FUNCTION
# ============================================================

def calculate_results():

    # --------------------------------------------------------
    # Composition score
    # --------------------------------------------------------

    total_composition = (
        main_component_percent +
        impurity_percent
    )

    if total_composition > 0:
        composition_score = (
            main_component_percent /
            total_composition
        ) * 100
    else:
        composition_score = 0


    # --------------------------------------------------------
    # Stability score
    # --------------------------------------------------------

    stability_score = (
        stability / 5
    ) * 100


    # --------------------------------------------------------
    # Reactivity score
    # --------------------------------------------------------

    # Lower unwanted reactivity = higher score
    reactivity_score = (
        (6 - reactivity) / 5
    ) * 100


    # --------------------------------------------------------
    # Homogeneity score
    # --------------------------------------------------------

    homogeneity_score = (
        homogeneity / 5
    ) * 100


    # --------------------------------------------------------
    # Moisture score
    # --------------------------------------------------------

    if moisture <= 5:
        moisture_score = 100

    elif moisture <= 10:
        moisture_score = 80

    elif moisture <= 15:
        moisture_score = 60

    elif moisture <= 20:
        moisture_score = 40

    else:
        moisture_score = 20


    # --------------------------------------------------------
    # Economic calculations
    # --------------------------------------------------------

    total_cost = (
        mining_cost
        + processing_cost
        + transport_cost
        + other_cost
    )

    estimated_margin = (
        market_price - total_cost
    )


    # --------------------------------------------------------
    # Economic score
    # --------------------------------------------------------

    if estimated_margin > 0:
        economic_score = 100

    else:
        economic_score = 0


    # --------------------------------------------------------
    # Overall quality score
    # --------------------------------------------------------

    quality_score = (
        composition_score * 0.25
        + stability_score * 0.15
        + reactivity_score * 0.15
        + homogeneity_score * 0.15
        + moisture_score * 0.10
        + economic_score * 0.20
    )

    quality_score = round(
        quality_score,
        2
    )


    # --------------------------------------------------------
    # Economic status
    # --------------------------------------------------------

    if estimated_margin > 0:

        economic_status = "ECONOMICALLY FEASIBLE"

    elif estimated_margin == 0:

        economic_status = "BREAK-EVEN"

    else:

        economic_status = "NOT ECONOMICALLY FEASIBLE"


    # --------------------------------------------------------
    # Quality classification
    # --------------------------------------------------------

    if quality_score >= 85:

        quality_class = "HIGH QUALITY"

    elif quality_score >= 70:

        quality_class = "GOOD QUALITY"

    elif quality_score >= 50:

        quality_class = "MODERATE QUALITY"

    else:

        quality_class = "LOW QUALITY"


    # --------------------------------------------------------
    # pH interpretation
    # --------------------------------------------------------

    if ph < 4:

        ph_status = "Strongly acidic"

    elif ph < 6:

        ph_status = "Acidic"

    elif ph <= 8:

        ph_status = "Approximately neutral"

    elif ph <= 10:

        ph_status = "Alkaline"

    else:

        ph_status = "Strongly alkaline"


    return {
        "composition_score": composition_score,
        "stability_score": stability_score,
        "reactivity_score": reactivity_score,
        "homogeneity_score": homogeneity_score,
        "moisture_score": moisture_score,
        "economic_score": economic_score,
        "total_cost": total_cost,
        "estimated_margin": estimated_margin,
        "quality_score": quality_score,
        "economic_status": economic_status,
        "quality_class": quality_class,
        "ph_status": ph_status
    }


# ============================================================
# 12. ANALYSIS BUTTON
# ============================================================

st.divider()

analyze = st.button(
    "🔍 ANALYZE MINERAL QUALITY",
    type="primary",
    use_container_width=True
)


# ============================================================
# 13. RESULTS
# ============================================================

if analyze:

    results = calculate_results()

    st.success("Mineral analysis completed successfully.")


    # ========================================================
    # MAIN RESULT
    # ========================================================

    st.header("9. Final Analysis Result")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Mineral Quality Score",
            f"{results['quality_score']:.2f}/100"
        )

    with col2:
        st.metric(
            "Quality Classification",
            results["quality_class"]
        )

    with col3:
        st.metric(
            "Economic Status",
            results["economic_status"]
        )


    # ========================================================
    # ECONOMIC SUMMARY
    # ========================================================

    st.subheader("💰 Economic Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Market Price / tonne",
            f"{market_price:,.2f}"
        )

    with col2:
        st.metric(
            "Total Cost / tonne",
            f"{results['total_cost']:,.2f}"
        )

    with col3:
        st.metric(
            "Estimated Margin / tonne",
            f"{results['estimated_margin']:,.2f}"
        )


    # ========================================================
    # CHEMICAL SUMMARY
    # ========================================================

    st.subheader("🧪 Chemical Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Composition Score",
            f"{results['composition_score']:.2f}/100"
        )

    with col2:
        st.metric(
            "Stability Score",
            f"{results['stability_score']:.2f}/100"
        )

    with col3:
        st.metric(
            "Reactivity Score",
            f"{results['reactivity_score']:.2f}/100"
        )

    st.write(
        f"*pH:* {ph:.2f} — {results['ph_status']}"
    )


    # ========================================================
    # PHYSICAL SUMMARY
    # ========================================================

    st.subheader("⚙️ Physical Characteristics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Particle Size",
            f"{particle_size:.2f} mm"
        )

    with col2:
        st.metric(
            "Bulk Density",
            f"{density:.2f} g/cm³"
        )

    with col3:
        st.metric(
            "Hardness",
            f"{hardness:.2f} Mohs"
        )

    with col4:
        st.metric(
            "Moisture",
            f"{moisture:.2f}%"
        )


    # ========================================================
    # QUALITY COMPONENTS
    # ========================================================

    st.subheader("📊 Quality Component Scores")

    categories = [
        "Composition",
        "Stability",
        "Reactivity",
        "Homogeneity",
        "Moisture",
        "Economics"
    ]

    values = [
        results["composition_score"],
        results["stability_score"],
        results["reactivity_score"],
        results["homogeneity_score"],
        results["moisture_score"],
        results["economic_score"]
    ]

    chart_data = pd.DataFrame(
        {
            "Parameter": categories,
            "Score": values
        }
    )

    st.bar_chart(
        chart_data,
        x="Parameter",
        y="Score"
    )


    # ========================================================
    # SCORE DETAILS
    # ========================================================

    st.subheader("📋 Detailed Scores")

    score_table = pd.DataFrame(
        {
            "Parameter": categories,
            "Score": [
                round(v, 2)
                for v in values
            ]
        }
    )

    st.dataframe(
        score_table,
        use_container_width=True,
        hide_index=True
    )


    # ========================================================
    # REPORT DATA
    # ========================================================

    report = pd.DataFrame(
        {
            "Parameter": [
                "Mineral",
                "Sample ID",
                "Main Component",
                "Main Component %",
                "Impurities %",
                "pH",
                "pH Classification",
                "Chemical Stability",
                "Stability Score",
                "Reactivity",
                "Reactivity Score",
                "Particle Size mm",
                "Bulk Density g/cm3",
                "Hardness Mohs",
                "Moisture %",
                "Moisture Score",
                "Homogeneity",
                "Homogeneity Score",
                "Market Price per Tonne",
                "Mining Cost per Tonne",
                "Processing Cost per Tonne",
                "Transportation Cost per Tonne",
                "Other Cost per Tonne",
                "Total Cost per Tonne",
                "Estimated Margin per Tonne",
                "Economic Score",
                "Economic Status",
                "Overall Quality Score",
                "Quality Class"
            ],

            "Value": [
                mineral_name,
                sample_id,
                main_component,
                main_component_percent,
                impurity_percent,
                ph,
                results["ph_status"],
                stability,
                results["stability_score"],
                reactivity,
                results["reactivity_score"],
                particle_size,
                density,
                hardness,
                moisture,
                results["moisture_score"],
                homogeneity,
                results["homogeneity_score"],
                market_price,
                mining_cost,
                processing_cost,
                transport_cost,
                other_cost,
                results["total_cost"],
                results["estimated_margin"],
                results["economic_score"],
                results["economic_status"],
                results["quality_score"],
                results["quality_class"]
            ]
        }
    )


    # ========================================================
    # DOWNLOAD REPORT
    # ========================================================

    st.subheader("📥 Download Analysis Report")

    csv_buffer = StringIO()

    report.to_csv(
        csv_buffer,
        index=False
    )

    st.download_button(
        label="⬇️ Download CSV Report",
        data=csv_buffer.getvalue(),
        file_name="mineral_quality_report.csv",
        mime="text/csv",
        use_container_width=True
    )


    # ========================================================
    # IMPORTANT NOTE
    # ========================================================

    st.info(
        """
        *Prototype note:* The quality score is a screening model
        based on the selected weights and scoring rules. The actual
        acceptable ranges and weights should be calibrated using
        laboratory results, mineral-specific specifications and
        plant/field data before using the system for operational or
        commercial decisions.
        """
    )


# ============================================================
# 14. INITIAL INFORMATION
# ============================================================

else:

    st.info(
        "Enter the mineral information above and click "
        "*ANALYZE MINERAL QUALITY* to generate the report."
    )

    st.caption(
        "This application does not require a CSV dataset. "
        "All calculations are performed from the values entered above."
    )