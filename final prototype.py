import io
import sqlite3
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

APP_VERSION = "7.0"
PROJECT_TITLE = "Mineral Quality Assessment and Economic Feasibility Decision-Support System"
DB_PATH = Path("mineral_quality_v7.db")

MINERALS = ["Iron Ore", "Limestone", "Bauxite", "Custom Mineral"]

DEFAULT_SPECS = {
    "Iron Ore": {
        "main_component": "Fe", "minimum_grade": 55.0, "maximum_moisture": 10.0,
        "minimum_ph": 5.0, "maximum_ph": 9.0,
        "source": "DEMO - replace with verified source", "source_type": "Reference required",
        "reference_id": ""
    },
    "Limestone": {
        "main_component": "CaCO3", "minimum_grade": 80.0, "maximum_moisture": 8.0,
        "minimum_ph": 6.0, "maximum_ph": 9.0,
        "source": "DEMO - replace with verified source", "source_type": "Reference required",
        "reference_id": ""
    },
    "Bauxite": {
        "main_component": "Al2O3", "minimum_grade": 40.0, "maximum_moisture": 12.0,
        "minimum_ph": 5.0, "maximum_ph": 9.0,
        "source": "DEMO - replace with verified source", "source_type": "Reference required",
        "reference_id": ""
    },
    "Custom Mineral": {
        "main_component": "Main Component", "minimum_grade": 50.0, "maximum_moisture": 10.0,
        "minimum_ph": 5.0, "maximum_ph": 9.0,
        "source": "DEMO - replace with verified source", "source_type": "Reference required",
        "reference_id": ""
    }
}

DEFAULT_WEIGHTS = {
    "Grade": 25.0, "pH": 10.0, "Chemical Stability": 10.0,
    "Chemical Reactivity": 10.0, "Moisture": 10.0,
    "Homogeneity": 10.0, "Economic Feasibility": 25.0
}

QUALITY_LABELS = ["HIGH", "GOOD", "MODERATE", "LOW"]

def get_conn():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    return con

def init_db():
    con = get_conn()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS app_config (
        config_key TEXT PRIMARY KEY,
        config_value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS specifications (
        mineral TEXT PRIMARY KEY,
        main_component TEXT NOT NULL,
        minimum_grade REAL NOT NULL,
        maximum_moisture REAL NOT NULL,
        minimum_ph REAL NOT NULL,
        maximum_ph REAL NOT NULL,
        source TEXT,
        source_type TEXT,
        reference_id TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS weights (
        weight_name TEXT PRIMARY KEY,
        weight_value REAL NOT NULL,
        version INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS samples (
        sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        sample_date TEXT NOT NULL,
        mineral TEXT NOT NULL,
        location TEXT NOT NULL,
        batch_no TEXT,
        component TEXT NOT NULL,
        component_percent REAL NOT NULL,
        impurity TEXT,
        impurity_percent REAL NOT NULL DEFAULT 0,
        ph REAL NOT NULL,
        stability REAL NOT NULL,
        reactivity REAL NOT NULL,
        homogeneity REAL NOT NULL,
        particle_size REAL,
        bulk_density REAL,
        hardness REAL,
        moisture REAL NOT NULL,
        selling_price REAL NOT NULL DEFAULT 0,
        mining_cost REAL NOT NULL DEFAULT 0,
        processing_cost REAL NOT NULL DEFAULT 0,
        transport_cost REAL NOT NULL DEFAULT 0,
        other_cost REAL NOT NULL DEFAULT 0,
        total_cost REAL NOT NULL,
        margin REAL NOT NULL,
        margin_percent REAL NOT NULL,
        grade_score REAL NOT NULL,
        ph_score REAL NOT NULL,
        stability_score REAL NOT NULL,
        reactivity_score REAL NOT NULL,
        moisture_score REAL NOT NULL,
        homogeneity_score REAL NOT NULL,
        economic_score REAL NOT NULL,
        overall_score REAL NOT NULL,
        quality_class TEXT NOT NULL,
        grade_status TEXT NOT NULL,
        moisture_status TEXT NOT NULL,
        ph_status TEXT NOT NULL,
        compliance_status TEXT NOT NULL,
        specification_source TEXT,
        specification_source_type TEXT,
        specification_reference TEXT,
        specification_version INTEGER,
        weight_version INTEGER,
        reference_quality_class TEXT,
        validation_status TEXT,
        validation_notes TEXT,
        data_source TEXT NOT NULL,
        test_method TEXT NOT NULL,
        notes TEXT
    );
    """)
    now = datetime.now().isoformat(timespec="seconds")
    for k, v in DEFAULT_WEIGHTS.items():
        con.execute(
            "INSERT OR IGNORE INTO weights(weight_name, weight_value, version, updated_at) VALUES(?,?,?,?)",
            (k, v, 1, now)
        )
    for mineral, s in DEFAULT_SPECS.items():
        con.execute("""
            INSERT OR IGNORE INTO specifications
            (mineral, main_component, minimum_grade, maximum_moisture, minimum_ph,
             maximum_ph, source, source_type, reference_id, version, updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (
            mineral, s["main_component"], s["minimum_grade"], s["maximum_moisture"],
            s["minimum_ph"], s["maximum_ph"], s["source"], s["source_type"],
            s["reference_id"], 1, now
        ))
    con.commit()
    con.close()

init_db()

def clamp(x, lo=0.0, hi=100.0):
    return float(max(lo, min(hi, float(x))))

def score_grade(value, minimum):
    return 0.0 if minimum <= 0 else clamp(value / minimum * 100)

def score_moisture(value, maximum):
    if maximum <= 0:
        return 100.0 if value <= 0 else 0.0
    return 100.0 if value <= maximum else clamp(maximum / value * 100)

def score_ph(value, minimum, maximum):
    if minimum <= value <= maximum:
        return 100.0
    distance = minimum - value if value < minimum else value - maximum
    return clamp(100 - distance * 20)

def score_stability(value):
    return clamp(value / 5 * 100)

def score_reactivity(value):
    # Project assumption: lower reactivity is better.
    return clamp((6 - value) / 5 * 100)

def score_homogeneity(value):
    return clamp(value / 5 * 100)

def score_economics(margin, selling_price):
    if selling_price <= 0:
        return 0.0
    # Break-even = 50; increasing positive margin approaches 100.
    return clamp(50 + (margin / selling_price) * 50)

def calculate_scores(spec, grade, ph, stability, reactivity, moisture, homogeneity,
                     price, total_cost, weights):
    scores = {
        "Grade": score_grade(grade, spec["minimum_grade"]),
        "pH": score_ph(ph, spec["minimum_ph"], spec["maximum_ph"]),
        "Chemical Stability": score_stability(stability),
        "Chemical Reactivity": score_reactivity(reactivity),
        "Moisture": score_moisture(moisture, spec["maximum_moisture"]),
        "Homogeneity": score_homogeneity(homogeneity),
        "Economic Feasibility": score_economics(price - total_cost, price),
    }
    total_weight = sum(weights.values())
    overall = sum(scores[k] * weights[k] for k in scores) / total_weight if total_weight else 0
    return scores, clamp(overall)

def quality_class(score):
    if score >= 85:
        return "HIGH"
    if score >= 70:
        return "GOOD"
    if score >= 50:
        return "MODERATE"
    return "LOW"

def compliance(spec, grade, moisture, ph):
    gs = "PASS" if grade >= spec["minimum_grade"] else "FAIL"
    ms = "PASS" if moisture <= spec["maximum_moisture"] else "FAIL"
    ps = "PASS" if spec["minimum_ph"] <= ph <= spec["maximum_ph"] else "FAIL"
    status = "COMPLIANT" if gs == ms == ps == "PASS" else "REVIEW"
    return gs, ms, ps, status

def validate_reference(predicted, reference):
    if not reference:
        return "NOT VALIDATED", "No independent reference class supplied."
    ref = str(reference).strip().upper()
    if ref not in QUALITY_LABELS:
        return "INVALID REFERENCE", "Reference class must be HIGH, GOOD, MODERATE or LOW."
    if predicted == ref:
        return "MATCH", "Application classification matches the independent reference class."
    return "MISMATCH", f"Application={predicted}; independent reference={ref}."

def get_specs():
    con = get_conn()
    df = pd.read_sql_query("SELECT * FROM specifications ORDER BY mineral", con)
    con.close()
    return {r["mineral"]: r.to_dict() for _, r in df.iterrows()}

def get_weights():
    con = get_conn()
    rows = con.execute("SELECT weight_name, weight_value FROM weights ORDER BY rowid").fetchall()
    con.close()
    return {k: float(v) for k, v in rows}

def get_weight_version():
    con = get_conn()
    v = con.execute("SELECT COALESCE(MAX(version),1) FROM weights").fetchone()[0]
    con.close()
    return int(v)

def get_df():
    con = get_conn()
    df = pd.read_sql_query("SELECT * FROM samples ORDER BY sample_id DESC", con)
    con.close()
    return df

def save_weights(weights):
    con = get_conn()
    now = datetime.now().isoformat(timespec="seconds")
    current = get_weight_version()
    new_version = current + 1
    for k, v in weights.items():
        con.execute(
            "UPDATE weights SET weight_value=?, version=?, updated_at=? WHERE weight_name=?",
            (float(v), new_version, now, k)
        )
    con.commit()
    con.close()

def save_spec(mineral, values):
    con = get_conn()
    old = con.execute("SELECT COALESCE(version,0) FROM specifications WHERE mineral=?", (mineral,)).fetchone()
    version = (old[0] if old else 0) + 1
    now = datetime.now().isoformat(timespec="seconds")
    con.execute("""
        INSERT INTO specifications
        (mineral,main_component,minimum_grade,maximum_moisture,minimum_ph,maximum_ph,
         source,source_type,reference_id,version,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(mineral) DO UPDATE SET
          main_component=excluded.main_component,
          minimum_grade=excluded.minimum_grade,
          maximum_moisture=excluded.maximum_moisture,
          minimum_ph=excluded.minimum_ph,
          maximum_ph=excluded.maximum_ph,
          source=excluded.source,
          source_type=excluded.source_type,
          reference_id=excluded.reference_id,
          version=excluded.version,
          updated_at=excluded.updated_at
    """, (
        mineral, values["main_component"], values["minimum_grade"], values["maximum_moisture"],
        values["minimum_ph"], values["maximum_ph"], values["source"], values["source_type"],
        values["reference_id"], version, now
    ))
    con.commit()
    con.close()

def insert_sample(record):
    columns = list(record.keys())
    placeholders = ",".join(["?"] * len(columns))
    con = get_conn()
    cur = con.execute(
        f"INSERT INTO samples ({','.join(columns)}) VALUES ({placeholders})",
        [record[c] for c in columns]
    )
    sample_id = cur.lastrowid
    con.commit()
    con.close()
    return sample_id

def audit_data(df):
    checks = []
    required = ["mineral","location","component_percent","moisture","ph","stability","reactivity","homogeneity"]
    missing = [c for c in required if c not in df.columns]
    checks.append(["Required columns", "PASS" if not missing else "FAIL", "All present" if not missing else ", ".join(missing)])
    dup = int(df.duplicated().sum())
    checks.append(["Duplicate rows", "PASS" if dup == 0 else "REVIEW", dup])
    ranges = {
        "component_percent": (0,100), "moisture": (0,100), "ph": (0,14),
        "stability": (1,5), "reactivity": (1,5), "homogeneity": (1,5)
    }
    for col,(lo,hi) in ranges.items():
        if col in df:
            s = pd.to_numeric(df[col], errors="coerce")
            bad = int(s.isna().sum() + ((s < lo) | (s > hi)).sum())
            checks.append([f"{col} valid range", "PASS" if bad == 0 else "FAIL", bad])
    return pd.DataFrame(checks, columns=["Check","Status","Result"])

def cv(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 2 or s.mean() == 0:
        return np.nan
    return float(s.std(ddof=1) / abs(s.mean()) * 100)

def make_pdf(row):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(PROJECT_TITLE, styles["Title"]),
        Paragraph(f"Application Version: {APP_VERSION}", styles["Normal"]),
        Spacer(1, 10)
    ]
    data = [
        ["Field","Value"],
        ["Sample ID", str(row.get("sample_id",""))],
        ["Date", str(row.get("sample_date",""))],
        ["Mineral", str(row.get("mineral",""))],
        ["Location", str(row.get("location",""))],
        ["Main component", f"{row.get('component','')} ({float(row.get('component_percent',0)):.2f}%)"],
        ["pH", f"{float(row.get('ph',0)):.2f}"],
        ["Moisture", f"{float(row.get('moisture',0)):.2f}%"],
        ["Total cost / t", f"{float(row.get('total_cost',0)):.2f}"],
        ["Margin / t", f"{float(row.get('margin',0)):.2f}"],
        ["Overall score", f"{float(row.get('overall_score',0)):.2f}/100"],
        ["Quality class", str(row.get('quality_class',''))],
        ["Compliance", str(row.get('compliance_status',''))],
        ["Validation", str(row.get('validation_status',''))],
        ["Specification", str(row.get('specification_source',''))],
        ["Specification reference", str(row.get('specification_reference',''))],
        ["Data source", str(row.get('data_source',''))],
        ["Test method", str(row.get('test_method',''))],
    ]
    t = Table(data, colWidths=[160,350])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")
    ]))
    story += [t, Spacer(1,12),
        Paragraph("This is a decision-support output. It does not replace certified laboratory testing, applicable standards, statutory requirements or professional engineering judgement.", styles["BodyText"])]
    doc.build(story)
    return buf.getvalue()

def template_df():
    return pd.DataFrame(columns=[
        "sample_date","mineral","location","batch_no","component","component_percent",
        "impurity","impurity_percent","ph","stability","reactivity","homogeneity",
        "particle_size","bulk_density","hardness","moisture","selling_price",
        "mining_cost","processing_cost","transport_cost","other_cost",
        "reference_quality_class","data_source","test_method","notes"
    ])

def build_record(r, specs, weights):
    mineral = str(r["mineral"]).strip()
    if mineral not in specs:
        raise ValueError(f"Mineral '{mineral}' is not configured.")
    spec = specs[mineral]
    location = str(r.get("location","")).strip()
    if not location:
        raise ValueError("Location is required.")
    def f(name, default=0.0):
        v = r.get(name, default)
        if pd.isna(v) or str(v).strip() == "":
            return float(default)
        return float(v)
    grade, moisture, ph = f("component_percent"), f("moisture"), f("ph")
    stability, reactivity, homogeneity = f("stability"), f("reactivity"), f("homogeneity")
    impurity_pct = f("impurity_percent")
    if not 0 <= grade <= 100 or not 0 <= moisture <= 100 or not 0 <= ph <= 14:
        raise ValueError("Grade/moisture/pH outside allowed range.")
    if not all(1 <= x <= 5 for x in [stability,reactivity,homogeneity]):
        raise ValueError("Stability/reactivity/homogeneity must be 1–5.")
    if grade + impurity_pct > 100:
        raise ValueError("Component % + impurity % cannot exceed 100%.")
    price, mining = f("selling_price"), f("mining_cost")
    processing, transport, other = f("processing_cost"), f("transport_cost"), f("other_cost")
    total_cost = mining + processing + transport + other
    margin = price - total_cost
    margin_pct = margin / price * 100 if price > 0 else 0
    scores, overall = calculate_scores(
        spec, grade, ph, stability, reactivity, moisture, homogeneity, price, total_cost, weights
    )
    qclass = quality_class(overall)
    gs, ms, ps, comp = compliance(spec, grade, moisture, ph)
    ref = str(r.get("reference_quality_class","") or "").strip().upper()
    val, note = validate_reference(qclass, ref)
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "sample_date": str(r.get("sample_date", date.today())),
        "mineral": mineral, "location": location,
        "batch_no": str(r.get("batch_no","") or ""),
        "component": str(r.get("component",spec["main_component"]) or spec["main_component"]),
        "component_percent": grade, "impurity": str(r.get("impurity","") or ""),
        "impurity_percent": impurity_pct, "ph": ph, "stability": stability,
        "reactivity": reactivity, "homogeneity": homogeneity,
        "particle_size": f("particle_size"), "bulk_density": f("bulk_density"),
        "hardness": f("hardness"), "moisture": moisture, "selling_price": price,
        "mining_cost": mining, "processing_cost": processing, "transport_cost": transport,
        "other_cost": other, "total_cost": total_cost, "margin": margin,
        "margin_percent": margin_pct, "grade_score": scores["Grade"],
        "ph_score": scores["pH"], "stability_score": scores["Chemical Stability"],
        "reactivity_score": scores["Chemical Reactivity"], "moisture_score": scores["Moisture"],
        "homogeneity_score": scores["Homogeneity"], "economic_score": scores["Economic Feasibility"],
        "overall_score": overall, "quality_class": qclass, "grade_status": gs,
        "moisture_status": ms, "ph_status": ps, "compliance_status": comp,
        "specification_source": spec["source"], "specification_source_type": spec["source_type"],
        "specification_reference": spec["reference_id"], "specification_version": int(spec["version"]),
        "weight_version": get_weight_version(), "reference_quality_class": ref,
        "validation_status": val, "validation_notes": note,
        "data_source": str(r.get("data_source","") or ""),
        "test_method": str(r.get("test_method","") or ""),
        "notes": str(r.get("notes","") or "")
    }

def sidebar():
    st.sidebar.title("⛏️ Mineral QA V7")
    st.sidebar.caption(f"Version {APP_VERSION}")
    return st.sidebar.radio("Navigation", [
        "🔬 New Sample","📊 Dashboard","📈 Statistics","📥 Excel Import",
        "💰 Economics","⚙️ Specifications","🔬 Validation & Evidence",
        "🧪 Data Quality","📚 Methodology","ℹ️ Project Information"
    ])

st.set_page_config(page_title="Mineral Quality Assessment V7", page_icon="⛏️", layout="wide")
st.title("⛏️ Mineral Quality Assessment & Economic Feasibility")
st.caption(f"{PROJECT_TITLE} • V{APP_VERSION}")

specs = get_specs()
weights = get_weights()
page = sidebar()

if page == "🔬 New Sample":
    st.header("New Mineral Sample")
    mineral = st.selectbox("Mineral", list(specs.keys()))
    spec = specs[mineral]
    with st.expander("Specification currently applied", expanded=True):
        st.info(
            f"Component: {spec['main_component']} | Grade ≥ {spec['minimum_grade']}% | "
            f"Moisture ≤ {spec['maximum_moisture']}% | pH {spec['minimum_ph']}–{spec['maximum_ph']}"
        )
        st.caption(f"Source: {spec['source']} | Reference: {spec['reference_id'] or 'Not entered'} | Version: {spec['version']}")
    with st.form("new_sample"):
        c1,c2,c3 = st.columns(3)
        with c1:
            location = st.text_input("Location *")
            batch = st.text_input("Batch / Lot No.")
            sample_date = st.date_input("Sample Date", date.today())
        with c2:
            component = st.text_input("Main Component", spec["main_component"])
            grade = st.number_input("Main Component %",0.0,100.0,float(spec["minimum_grade"]),0.01)
            impurity = st.text_input("Main Impurity")
            impurity_pct = st.number_input("Impurity %",0.0,100.0,0.0,0.01)
        with c3:
            ph = st.number_input("pH",0.0,14.0,7.0,0.01)
            moisture = st.number_input("Moisture %",0.0,100.0,min(spec["maximum_moisture"],5.0),0.01)
            stability = st.slider("Chemical Stability (1–5)",1.0,5.0,4.0,0.1)
            reactivity = st.slider("Chemical Reactivity (1–5)",1.0,5.0,2.0,0.1)
            homogeneity = st.slider("Homogeneity (1–5)",1.0,5.0,4.0,0.1)
        st.subheader("Physical Characteristics")
        p1,p2,p3 = st.columns(3)
        with p1: particle = st.number_input("Particle Size (mm)",0.0,10000.0,0.0,0.01)
        with p2: density = st.number_input("Bulk Density (t/m³)",0.0,20.0,0.0,0.01)
        with p3: hardness = st.number_input("Hardness",0.0,20.0,0.0,0.01)
        st.subheader("Economic Feasibility")
        e1,e2,e3,e4,e5 = st.columns(5)
        with e1: price = st.number_input("Selling Price / t",0.0,1e9,0.0,0.01)
        with e2: mining = st.number_input("Mining Cost / t",0.0,1e9,0.0,0.01)
        with e3: processing = st.number_input("Processing Cost / t",0.0,1e9,0.0,0.01)
        with e4: transport = st.number_input("Transport Cost / t",0.0,1e9,0.0,0.01)
        with e5: other = st.number_input("Other Cost / t",0.0,1e9,0.0,0.01)
        st.subheader("Evidence & Validation")
        d1,d2 = st.columns(2)
        with d1:
            data_source = st.text_input("Data Source *", placeholder="Laboratory / field / published dataset")
            test_method = st.text_input("Test Method / Instrument *", placeholder="XRF / pH meter / moisture oven")
        with d2:
            reference_class = st.selectbox("Independent Reference Quality Class",[""]+QUALITY_LABELS)
            notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Sample & Calculate")
    if submitted:
        if not location.strip() or not data_source.strip() or not test_method.strip():
            st.error("Location, Data Source and Test Method are required.")
        elif grade + impurity_pct > 100:
            st.error("Main component % + impurity % cannot exceed 100%.")
        else:
            raw = {
                "sample_date": sample_date, "mineral": mineral, "location": location,
                "batch_no": batch, "component": component, "component_percent": grade,
                "impurity": impurity, "impurity_percent": impurity_pct, "ph": ph,
                "stability": stability, "reactivity": reactivity, "homogeneity": homogeneity,
                "particle_size": particle, "bulk_density": density, "hardness": hardness,
                "moisture": moisture, "selling_price": price, "mining_cost": mining,
                "processing_cost": processing, "transport_cost": transport, "other_cost": other,
                "reference_quality_class": reference_class, "data_source": data_source,
                "test_method": test_method, "notes": notes
            }
            record = build_record(raw, specs, weights)
            sid = insert_sample(record)
            st.success(f"Sample saved. Sample ID: {sid}")
            st.metric("Overall Score", f"{record['overall_score']:.2f}/100")
            st.metric("Quality Class", record["quality_class"])
            st.metric("Compliance", record["compliance_status"])
            st.metric("Validation", record["validation_status"])
            score_map = {
                "Grade": record["grade_score"],
                "pH": record["ph_score"],
                "Chemical Stability": record["stability_score"],
                "Chemical Reactivity": record["reactivity_score"],
                "Moisture": record["moisture_score"],
                "Homogeneity": record["homogeneity_score"],
                "Economic Feasibility": record["economic_score"],
            }
            st.subheader("Score Breakdown")
            st.dataframe(pd.DataFrame({
                "Dimension": list(score_map.keys()),
                "Score": list(score_map.values()),
                "Weight (%)": [weights[k] for k in score_map]
            }).round(3), use_container_width=True, hide_index=True)
            latest = get_df().iloc[0].to_dict()
            st.download_button("📄 Download PDF Report", make_pdf(latest),
                               f"mineral_quality_report_{sid}.pdf","application/pdf")

elif page == "📊 Dashboard":
    st.header("Quality Dashboard")
    df = get_df()
    if df.empty:
        st.info("No samples yet. Add a sample or import the supplied demo dataset.")
    else:
        minerals = sorted(df.mineral.unique())
        selected = st.multiselect("Minerals", minerals, default=minerals)
        x = df[df.mineral.isin(selected)].copy()
        a,b,c,d = st.columns(4)
        a.metric("Samples", len(x))
        b.metric("Average Score", f"{x.overall_score.mean():.2f}")
        c.metric("High / Good", int(x.quality_class.isin(["HIGH","GOOD"]).sum()))
        d.metric("Validation Matches", int((x.validation_status=="MATCH").sum()))
        st.subheader("Quality Distribution")
        st.bar_chart(x.quality_class.value_counts().reindex(QUALITY_LABELS).fillna(0))
        st.subheader("Mineral-wise Average")
        st.bar_chart(x.groupby("mineral").overall_score.mean().sort_values(ascending=False))
        st.subheader("Records")
        st.dataframe(x, use_container_width=True, hide_index=True)
        sid = st.selectbox("PDF Report Sample ID", x.sample_id.tolist())
        row = x[x.sample_id == sid].iloc[0].to_dict()
        st.download_button("📄 Download Selected PDF", make_pdf(row),
                           f"mineral_quality_report_{sid}.pdf","application/pdf")

elif page == "📈 Statistics":
    st.header("Statistical Analysis")
    df = get_df()
    if df.empty:
        st.info("Add data first.")
    else:
        cols = [c for c in ["component_percent","impurity_percent","ph","moisture","stability","reactivity","homogeneity","overall_score","margin_percent"] if c in df]
        st.subheader("Descriptive Statistics")
        st.dataframe(df[cols].describe().T.round(3), use_container_width=True)
        st.subheader("Coefficient of Variation")
        st.dataframe(pd.DataFrame({"Mean":df[cols].mean(),"Std Dev":df[cols].std(),"CV %":[cv(df[c]) for c in cols]}).round(3), use_container_width=True)
        st.subheader("Correlation with Overall Score")
        st.dataframe(df[cols].corr(numeric_only=True)["overall_score"].sort_values(ascending=False).to_frame("Correlation").round(3), use_container_width=True)
        feature = st.selectbox("Scatter Variable", [c for c in cols if c != "overall_score"])
        st.scatter_chart(df[[feature,"overall_score"]].dropna().set_index(feature))

elif page == "📥 Excel Import":
    st.header("Excel / CSV Import")
    st.caption("Use real, traceable laboratory/field/published data for your final project. The included demo data is synthetic.")
    tmpl = template_df().to_csv(index=False).encode()
    st.download_button("⬇️ Download CSV Template", tmpl, "mineral_quality_template.csv", "text/csv")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)
            st.dataframe(df.head(20), use_container_width=True)
            if st.button("Validate & Import"):
                good, bad = [], []
                for idx, row in df.iterrows():
                    try:
                        good.append(build_record(row, specs, weights))
                    except Exception as e:
                        bad.append({"row": idx+2, "reason": str(e)})
                if good:
                    con = get_conn()
                    cols = list(good[0].keys())
                    placeholders = ",".join(["?"]*len(cols))
                    con.executemany(f"INSERT INTO samples ({','.join(cols)}) VALUES ({placeholders})",
                                    [[r[c] for c in cols] for r in good])
                    con.commit(); con.close()
                    st.success(f"Imported {len(good)} valid rows.")
                if bad:
                    st.warning(f"Rejected {len(bad)} rows.")
                    st.dataframe(pd.DataFrame(bad), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read file: {e}")

elif page == "💰 Economics":
    st.header("Economic Feasibility & Sensitivity")
    df = get_df()
    if df.empty:
        st.info("Add samples first.")
    else:
        st.dataframe(df[["sample_id","mineral","selling_price","total_cost","margin","margin_percent","economic_score"]], use_container_width=True)
        sid = st.selectbox("Select Sample", df.sample_id.tolist())
        r = df[df.sample_id == sid].iloc[0]
        changes = [-20,-10,-5,0,5,10,20]
        rows = []
        for ch in changes:
            p = float(r.selling_price) * (1+ch/100)
            m = p - float(r.total_cost)
            rows.append({"Price Change %":ch,"Scenario Price":p,"Margin":m,"Economic Score":score_economics(m,p)})
        s = pd.DataFrame(rows)
        st.dataframe(s.round(3), use_container_width=True)
        st.line_chart(s.set_index("Price Change %")[["Margin","Economic Score"]])

elif page == "⚙️ Specifications":
    st.header("Specifications & Scoring Weights")
    mineral = st.selectbox("Mineral", list(specs.keys()))
    s = specs[mineral]
    with st.form("spec_edit"):
        a,b = st.columns(2)
        with a:
            main = st.text_input("Main Component", s["main_component"])
            min_grade = st.number_input("Minimum Grade %",0.0,100.0,float(s["minimum_grade"]),0.01)
            max_m = st.number_input("Maximum Moisture %",0.0,100.0,float(s["maximum_moisture"]),0.01)
        with b:
            min_ph = st.number_input("Minimum pH",0.0,14.0,float(s["minimum_ph"]),0.01)
            max_ph = st.number_input("Maximum pH",0.0,14.0,float(s["maximum_ph"]),0.01)
            source = st.text_input("Source / Standard / Lab Reference", s["source"])
            ref_id = st.text_input("Reference ID / URL / Report No.", s["reference_id"])
            source_type = st.text_input("Source Type", s["source_type"])
        save = st.form_submit_button("Save Specification")
    if save:
        save_spec(mineral, {
            "main_component":main,"minimum_grade":min_grade,"maximum_moisture":max_m,
            "minimum_ph":min_ph,"maximum_ph":max_ph,"source":source,
            "reference_id":ref_id,"source_type":source_type
        })
        st.success("Specification saved with a new version.")
        st.rerun()
    st.subheader("Scoring Weights")
    st.caption("These are project-defined methodology choices, not universal industry standards.")
    neww = {}
    total = 0
    for k,v in weights.items():
        neww[k] = st.number_input(k,0.0,100.0,float(v),0.5,key="weight_"+k)
        total += neww[k]
    st.metric("Weight Total", f"{total:.1f}%")
    if st.button("Save Weights"):
        if total <= 0:
            st.error("At least one weight must be greater than zero.")
        else:
            save_weights(neww)
            st.success("Weights saved with a new methodology version.")
            st.rerun()

elif page == "🔬 Validation & Evidence":
    st.header("Scientific Validation & Evidence")
    df = get_df()
    if df.empty:
        st.info("No samples yet.")
    else:
        valid = df[df.reference_quality_class.fillna("").astype(str).str.strip() != ""].copy()
        st.metric("Samples with Independent Reference", len(valid))
        if not valid.empty:
            valid["Match"] = valid.quality_class.str.upper() == valid.reference_quality_class.str.upper()
            st.metric("Classification Agreement", f"{valid.Match.mean()*100:.1f}%")
            cm = pd.crosstab(valid.reference_quality_class.str.upper(), valid.quality_class.str.upper()).reindex(
                index=QUALITY_LABELS, columns=QUALITY_LABELS, fill_value=0
            )
            st.dataframe(cm, use_container_width=True)
            st.dataframe(valid[["sample_id","mineral","overall_score","quality_class","reference_quality_class","validation_status","validation_notes","data_source","test_method"]], use_container_width=True)
        else:
            st.warning("No independent reference classifications have been entered.")
        st.subheader("Evidence Coverage")
        audit = []
        for col in ["data_source","test_method","specification_reference"]:
            filled = int(df[col].fillna("").astype(str).str.strip().ne("").sum())
            audit.append([col, filled, len(df), filled/len(df)*100])
        st.dataframe(pd.DataFrame(audit, columns=["Field","Filled","Total","Coverage %"]).round(2), use_container_width=True)

elif page == "🧪 Data Quality":
    st.header("Data Quality Audit")
    df = get_df()
    if df.empty:
        st.info("No samples yet.")
    else:
        st.dataframe(audit_data(df), use_container_width=True, hide_index=True)
        st.subheader("Missing-value summary")
        miss = df.isna().sum().sort_values(ascending=False).to_frame("Missing")
        miss["Coverage %"] = (1 - miss["Missing"]/len(df))*100
        st.dataframe(miss.round(2), use_container_width=True)
        st.download_button("⬇️ Download Full Dataset", df.to_csv(index=False).encode(),
                           "mineral_quality_results.csv","text/csv")

elif page == "📚 Methodology":
    st.header("Methodology")
    st.markdown("""
### 1. Assessment dimensions
The model evaluates grade, pH, chemical stability, chemical reactivity, moisture,
homogeneity and economic feasibility.

### 2. Normalization
Each dimension is converted to a 0–100 score. The overall score is the weighted
average of these normalized scores.

### 3. Project assumptions
- Grade: higher main-component concentration increases the score.
- Moisture: at or below the configured maximum receives 100.
- pH: values inside the configured range receive 100; values outside are penalized.
- Stability: 1–5, where 5 is better.
- Reactivity: 1–5, where lower reactivity is treated as better. This is a project assumption.
- Homogeneity: 1–5, where 5 is better.
- Economics: selling price minus mining, processing, transport and other costs.
- Economic score uses break-even = 50 and increases with positive margin.

### 4. Quality classes
**HIGH:** 85–100  
**GOOD:** 70–84.99  
**MODERATE:** 50–69.99  
**LOW:** below 50

These thresholds are project-defined and must not be presented as universal industry standards.

### 5. Reproducibility
Each saved sample records the specification version and weight version used for its
calculation. This prevents later changes from silently changing historical results.

### 6. Validation
Independent reference classes can be entered. The application reports agreement and a
confusion matrix. Agreement is evidence for comparison, not proof that the model is
scientifically valid.

### 7. Data requirements
For the final-year project, use real traceable data where available and record the
source, test method/instrument, sample date and specification reference.
""")

elif page == "ℹ️ Project Information":
    st.header("Project Information")
    st.markdown(f"""
**Project Title:** {PROJECT_TITLE}

**Application Version:** {APP_VERSION}

**Technology:** Python, Streamlit, Pandas, NumPy, SQLite, ReportLab

**Scope:** Mineral/ore quality assessment and economic feasibility decision support.

**Main inputs:** chemical composition, pH, moisture, stability, reactivity,
homogeneity, physical characteristics and cost/revenue data.

**Outputs:** normalized scores, overall quality class, specification compliance,
economic feasibility, validation agreement, statistics, audit results and PDF reports.

**Important limitation:** This is a decision-support prototype. It does not replace
certified laboratory testing, applicable standards, statutory requirements or
professional engineering judgement.

**Demo data:** Any supplied demo dataset is synthetic and must be replaced or clearly
labelled before final submission.
""")
