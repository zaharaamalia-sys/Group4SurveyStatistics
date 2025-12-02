# FinalProjectStatistics8.py
# FINAL version — Ultra Pink Dashboard + Robust Cleaning + Correlations + PDF (Pink)
# Requirements: streamlit pandas numpy scipy matplotlib seaborn fpdf openpyxl xlrd

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
from scipy import stats
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile, os
from datetime import datetime
from textwrap import shorten

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="Final Project Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Language pack (ID/EN/CN)
# ---------------------------
LANG = {
    "id": {
        "title": "Dashboard Survei — Belanja Online vs Kontrol Keuangan",
        "subtitle": "Multi-bahasa, tema pink, PDF export. Pastikan file memiliki kolom Age, X1..X5, Y1..Y5 atau serupa.",
        "upload": "Unggah dataset (CSV / XLSX)",
        "overview": "Overview",
        "desc": "Statistik Deskriptif",
        "visual": "Visualisasi",
        "dist": "Distribusi & Outlier",
        "corr": "Analisis Korelasi",
        "assoc": "Analisis Asosiasi",
        "heatmap": "Heatmap",
        "pdf": "Laporan PDF (Pink)",
        "team": "Anggota Tim",
        "choose_col": "Pilih kolom untuk visualisasi",
        "choose_numeric": "Pilih kolom numerik (multi)",
        "no_numeric": "Tidak ada kolom numerik terdeteksi.",
        "hist_of": "Histogram dari",
        "no_outlier": "Tidak ada outlier ditemukan.",
        "outlier_found": "Outlier ditemukan:",
        "generate_pdf": "Buat & Unduh PDF",
        "upload_example": "Contoh template tersedia di sidebar."
    },
    "en": {
        "title": "Survey Dashboard — Online Shopping vs Financial Control",
        "subtitle": "Multi-language, pink theme, PDF export. Make sure file has Age, X1..X5, Y1..Y5 or similar.",
        "upload": "Upload dataset (CSV / XLSX)",
        "overview": "Overview",
        "desc": "Descriptive",
        "visual": "Visualization",
        "dist": "Distribution & Outliers",
        "corr": "Correlation Analysis",
        "assoc": "Association Analysis",
        "heatmap": "Heatmap",
        "pdf": "PDF Report (Pink)",
        "team": "Team Members",
        "choose_col": "Choose column for visualization",
        "choose_numeric": "Choose numeric columns (multi)",
        "no_numeric": "No numeric columns detected.",
        "hist_of": "Histogram of",
        "no_outlier": "No outliers found.",
        "outlier_found": "Outliers detected:",
        "generate_pdf": "Generate & Download PDF",
        "upload_example": "Sample template available in sidebar."
    },
    "cn": {
        "title": "调查仪表盘 — 网购习惯 vs 财务控制",
        "subtitle": "多语言、粉色主题、PDF 导出。确保文件包含 Age, X1..X5, Y1..Y5 等列。",
        "upload": "上传数据集 (CSV / XLSX)",
        "overview": "概览",
        "desc": "描述性统计",
        "visual": "可视化",
        "dist": "分布与离群值",
        "corr": "相关性分析",
        "assoc": "关联分析",
        "heatmap": "热力图",
        "pdf": "PDF 报告（粉色）",
        "team": "团队成员",
        "choose_col": "选择可视化列",
        "choose_numeric": "选择数值列（多选）",
        "no_numeric": "未检测到数值列。",
        "hist_of": "直方图：",
        "no_outlier": "未发现离群值。",
        "outlier_found": "检测到离群值：",
        "generate_pdf": "生成并下载 PDF",
        "upload_example": "侧栏提供示例模板。"
    }
}

# ---------------------------
# Sidebar: language, theme, sample template
# ---------------------------
lang_choice = st.sidebar.selectbox("Language / Bahasa / 中文", ["id", "en", "cn"],
                                   index=0,
                                   format_func=lambda x: {"id":"Bahasa Indonesia","en":"English","cn":"中文"}[x])
T = LANG[lang_choice]

theme_mode = st.sidebar.selectbox("Theme Mode", ["Light", "Dark"])
pink = "#ffd3e0"

# Ultra-pink CSS for Light
if theme_mode == "Light":
    st.markdown(f"""
        <style>
        .stApp {{ background: linear-gradient(180deg,#fff0f6,{pink}); }}
        .big-title {{ font-size:28px; font-weight:700; color:#9b0750; }}
        .sub-title {{ color:#4a154b; margin-bottom:16px; }}
        .card {{ background: white; border-radius:12px; padding:8px; box-shadow: 0 6px 18px rgba(155,7,80,0.08); }}
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background: #0f0b12; color: #f0e6ee; }
        .big-title { color: #ffb6d9; }
        .sub-title { color: #ff9fc9; margin-bottom:10px; }
        .card { background: #1b1220; border-radius:10px; padding:8px; }
        </style>
    """, unsafe_allow_html=True)

# Sample template for sidebar download
sample_df = pd.DataFrame({
    "NO":[1,2,3],
    "Age":[20,19,21],
    "Gender":["Laki-laki","Perempuan","Perempuan"],
    "X1":[3,2,3],"X2":[3,2,4],"X3":[3,4,3],"X4":[3,3,4],"X5":[2,3,4],
    "X_total":[14,12,18],
    "Y1":[3,4,3],"Y2":[3,3,4],"Y3":[3,3,4],"Y4":[3,4,4],"Y5":[4,3,4],
    "Y_total":[16,17,18]
})
st.sidebar.download_button("Download sample template (CSV)", sample_df.to_csv(index=False).encode("utf-8"), "template_survey.csv")
st.sidebar.caption(T["upload_example"])

# ---------------------------
# Helpers: cleaning, save fig, interpret
# ---------------------------
def clean_dataframe(raw_df):
    df = raw_df.copy()
    # Drop fully empty rows and columns
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")
    # Normalize column names
    df.columns = df.columns.astype(str).str.strip().str.replace(" ", "_").str.replace("-", "_")
    # Drop Unnamed columns
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    # Strip whitespace and fix thousand separators for string cells
    for c in df.columns:
        # only operate on object columns to avoid changing numeric types already
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip().str.replace("\xa0","")
            # replace commas used as decimal/comma thousands heuristics
            df[c] = df[c].str.replace(",", ".", regex=False)
    # Force convert known numeric-like columns to numeric
    numeric_candidates = ["Age", "Income",
                          "X1","X2","X3","X4","X5","X_total",
                          "Y1","Y2","Y3","Y4","Y5","Y_total"]
    # If column exists, coerce
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Also coerce any column where >50% values look numeric
    for col in df.columns:
        if df[col].dtype == object:
            coerced = pd.to_numeric(df[col], errors="coerce")
            ratio = coerced.notna().sum() / max(1, len(coerced))
            if ratio >= 0.6:
                df[col] = coerced
    # Drop rows that are empty after coercion
    df = df.dropna(axis=0, how="all")
    return df

def save_fig_to_tmp(fig):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp.name, bbox_inches="tight")
    plt.close(fig)
    return tmp.name

def add_image_pdf(pdf, img_path, x=15, w=180):
    try:
        pdf.image(img_path, x=x, w=w)
    except Exception:
        pass

def interpret_r(r):
    if pd.isna(r):
        return ""
    ar = abs(r)
    if ar < 0.2:
        return "very weak"
    elif ar < 0.4:
        return "weak"
    elif ar < 0.6:
        return "moderate"
    elif ar < 0.8:
        return "strong"
    else:
        return "very strong"

# ---------------------------
# App pages
# ---------------------------
pages = [
    T["overview"],
    T["desc"],
    T["visual"],
    T["dist"],
    T["corr"],
    T["assoc"],
    T["heatmap"],
    T["pdf"],
    T["team"]
]
page = st.sidebar.selectbox("Page", pages)

# Shared uploader (also available on overview)
uploaded = st.sidebar.file_uploader(T["upload"], type=["csv","xlsx","xls"], key="uploader_sidebar")

# If uploaded via sidebar, load and clean immediately
if uploaded is not None:
    try:
        if uploaded.name.lower().endswith(".csv"):
            raw = pd.read_csv(uploaded)
        else:
            raw = pd.read_excel(uploaded)
        df = clean_dataframe(raw)
        st.session_state["df"] = df
        st.success("Dataset loaded & cleaned.")
    except Exception as e:
        st.error(f"Error loading file: {e}")

# ---------------------------
# PAGE: Overview
# ---------------------------
if page == T["overview"]:
    st.markdown(f"<div class='big-title'>{T['title']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>{T['subtitle']}</div>", unsafe_allow_html=True)
    # upload widget here too
    uploaded_local = st.file_uploader(T["upload"], type=["csv","xlsx","xls"], key="uploader_local")
    used_file = uploaded_local if uploaded_local is not None else uploaded
    if used_file is not None:
        try:
            if used_file.name.lower().endswith(".csv"):
                raw = pd.read_csv(used_file)
            else:
                raw = pd.read_excel(used_file)
            df = clean_dataframe(raw)
            st.session_state["df"] = df
            st.success("Dataset loaded & cleaned.")
            st.dataframe(df.head())
            st.markdown("**Columns detected:**")
            st.write(list(df.columns))
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info(T["upload"])

# ---------------------------
# PAGE: Descriptive
# ---------------------------
elif page == T["desc"]:
    st.header(T["desc"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        num = df.select_dtypes(include=[np.number])
        if num.shape[1] == 0:
            st.warning(T["no_numeric"])
        else:
            st.dataframe(num.describe().T)

# ---------------------------
# PAGE: Visualization
# ---------------------------
elif page == T["visual"]:
    st.header(T["visual"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        cols = list(df.columns)
        col = st.selectbox(T["choose_col"], cols)
        if col:
            ser = df[col].dropna()
            if pd.api.types.is_numeric_dtype(ser):
                fig, ax = plt.subplots(figsize=(7,3))
                sns.histplot(ser, bins=5, kde=True, ax=ax)
                ax.set_title(f"{T['hist_of']} {col}")
                st.pyplot(fig)
                # bar of counts (rounded bins)
                fig2, ax2 = plt.subplots(figsize=(6,3))
                sns.histplot(ser, bins=5, ax=ax2)
                st.pyplot(fig2)
                # descriptive small
                st.write(ser.describe())
            else:
                fig, ax = plt.subplots(figsize=(6,3))
                ser.value_counts().plot(kind="bar", ax=ax)
                st.pyplot(fig)
                if ser.nunique() <= 10:
                    fig2, ax2 = plt.subplots(figsize=(4,4))
                    ser.value_counts().plot(kind="pie", autopct='%1.1f%%', ax=ax2)
                    ax2.set_ylabel("")
                    st.pyplot(fig2)

# ---------------------------
# PAGE: Distribution & Outlier
# ---------------------------
elif page == T["dist"]:
    st.header(T["dist"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num_cols:
            st.warning(T["no_numeric"])
        else:
            selected = st.multiselect(T["choose_numeric"], num_cols, default=num_cols[:5])
            if selected:
                cols_per_row = 2
                nsel = len(selected)
                rows = (nsel + cols_per_row - 1)//cols_per_row
                idx = 0
                for r in range(rows):
                    row_cols = st.columns(cols_per_row)
                    for cidx in range(cols_per_row):
                        if idx >= nsel:
                            break
                        cname = selected[idx]
                        with row_cols[cidx]:
                            st.subheader(f"{T['hist_of']} {cname}")
                            ser = df[cname].dropna()
                            fig, ax = plt.subplots(figsize=(5,3))
                            sns.histplot(ser, bins=5, kde=True, ax=ax)
                            st.pyplot(fig)
                            # boxplot
                            figb, axb = plt.subplots(figsize=(5,1.2))
                            sns.boxplot(x=ser, ax=axb)
                            st.pyplot(figb)
                            # outliers
                            Q1 = ser.quantile(0.25)
                            Q3 = ser.quantile(0.75)
                            IQR = Q3 - Q1
                            low = Q1 - 1.5*IQR
                            high = Q3 + 1.5*IQR
                            outliers = df[(df[cname] < low) | (df[cname] > high)][cname]
                            if outliers.empty:
                                st.success(T["no_outlier"])
                            else:
                                st.error(f"{T['outlier_found']} {len(outliers)}")
                                st.write(outliers.head(10))
                        idx += 1

# ---------------------------
# PAGE: Correlation (Pearson + Spearman + Kendall)
# ---------------------------
elif page == T["corr"]:
    st.header(T["corr"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) < 2:
            st.warning(T["no_numeric"])
        else:
            c1 = st.selectbox("Variable 1", num_cols, index=0)
            c2 = st.selectbox("Variable 2", num_cols, index=1)
            pair = df[[c1,c2]].dropna()
            if pair.shape[0] < 3:
                st.warning("Not enough paired observations (min 3).")
            else:
                # Pearson
                try:
                    r_p, p_p = stats.pearsonr(pair[c1], pair[c2])
                except Exception:
                    r_p, p_p = (np.nan, np.nan)
                # Spearman
                try:
                    r_s, p_s = stats.spearmanr(pair[c1], pair[c2])
                except Exception:
                    r_s, p_s = (np.nan, np.nan)
                # Kendall
                try:
                    r_k, p_k = stats.kendalltau(pair[c1], pair[c2])
                except Exception:
                    r_k, p_k = (np.nan, np.nan)

                st.subheader("Pearson")
                st.write(f"r = {r_p:.4f}, p = {p_p:.4f} — {interpret_r(r_p)}")
                st.subheader("Spearman")
                st.write(f"ρ = {r_s:.4f}, p = {p_s:.4f} — {interpret_r(r_s)}")
                st.subheader("Kendall")
                st.write(f"τ = {r_k:.4f}, p = {p_k:.4f} — {interpret_r(r_k)}")

                # scatter + regression line
                fig, ax = plt.subplots(figsize=(6,4))
                sns.regplot(x=pair[c1], y=pair[c2], ax=ax, scatter_kws={'alpha':0.6})
                ax.set_xlabel(c1); ax.set_ylabel(c2)
                st.pyplot(fig)

# ---------------------------
# PAGE: Automatic Association (summary + decision)
# ---------------------------
elif page == T["assoc"]:
    st.header(T["assoc"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) < 2:
            st.warning(T["no_numeric"])
        else:
            v1 = st.selectbox("Variable A", num_cols, index=0)
            v2 = st.selectbox("Variable B", num_cols, index=1)
            pair = df[[v1,v2]].dropna()
            if pair.shape[0] < 3:
                st.warning("Not enough paired observations.")
            else:
                r_p, p_p = stats.pearsonr(pair[v1], pair[v2])
                r_s, p_s = stats.spearmanr(pair[v1], pair[v2])
                r_k, p_k = stats.kendalltau(pair[v1], pair[v2])

                st.write("Pearson: r = {:.4f}, p = {:.4f} — {}".format(r_p, p_p, interpret_r(r_p)))
                st.write("Spearman: ρ = {:.4f}, p = {:.4f} — {}".format(r_s, p_s, interpret_r(r_s)))
                st.write("Kendall: τ = {:.4f}, p = {:.4f} — {}".format(r_k, p_k, interpret_r(r_k)))

                # Decision (alpha=0.05)
                alpha = 0.05
                st.markdown("**Hypothesis decision (α = 0.05)**")
                st.write(f"Pearson: {'Reject H0' if p_p < alpha else 'Fail to reject H0'}")
                st.write(f"Spearman: {'Reject H0' if p_s < alpha else 'Fail to reject H0'}")
                st.write(f"Kendall: {'Reject H0' if p_k < alpha else 'Fail to reject H0'}")

# ---------------------------
# PAGE: Heatmap
# ---------------------------
elif page == T["heatmap"]:
    st.header(T["heatmap"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) < 2:
            st.warning(T["no_numeric"])
        else:
            corr = df[num_cols].corr()
            fig, ax = plt.subplots(figsize=(10,8))
            sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdPu", center=0, ax=ax)
            st.pyplot(fig)

# ---------------------------
# PAGE: PDF (Pink theme)
# ---------------------------
elif page == T["pdf"]:
    st.header(T["pdf"])
    df = st.session_state.get("df", None)
    if df is None:
        st.info(T["upload"])
    else:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        include_hist = st.multiselect("Include histograms", numeric_cols, default=numeric_cols[:3])
        include_heat = st.checkbox("Include heatmap", value=True)
        include_scatter = st.checkbox("Include scatter (first pair)", value=True)
        author = st.text_input("Author / Nama Penulis", value="Team")
        title = st.text_input("Report title / Judul Laporan", value="Laporan Survei")

        if st.button(T["generate_pdf"]):
            with st.spinner("Generating PDF..."):
                pdf = FPDF(orientation="P", unit="mm", format="A4")
                pdf.set_auto_page_break(auto=True, margin=12)

                # Cover with pink background
                pdf.add_page()
                pdf.set_fill_color(255, 210, 224)
                pdf.rect(0, 0, 210, 297, style="F")
                pdf.set_font("Arial", "B", 18)
                pdf.set_text_color(120, 10, 60)
                pdf.cell(0, 14, title, ln=True, align="C")
                pdf.ln(4)
                pdf.set_font("Arial", size=11)
                pdf.set_text_color(80, 20, 50)
                pdf.cell(0, 8, f"Author: {author}", ln=True)
                pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
                pdf.ln(6)

                tmp_files = []
                # Summary stats text
                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "Summary statistics", ln=True)
                pdf.set_font("Arial", size=10)
                try:
                    numdf = df.select_dtypes(include=[np.number])
                    pdf.multi_cell(0, 6, numdf.describe().to_string())
                except Exception:
                    pdf.multi_cell(0, 6, "No numeric data summary available.")

                # Histograms
                for col in include_hist:
                    try:
                        fig = plt.figure(figsize=(6,3))
                        sns.histplot(df[col].dropna(), bins=5, kde=True)
                        plt.title(col)
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        fig.savefig(tmp.name, bbox_inches="tight")
                        plt.close(fig)
                        tmp_files.append(tmp.name)
                        pdf.add_page()
                        add_image_pdf(pdf, tmp.name, x=15, w=180)
                    except Exception:
                        pass

                # Heatmap
                if include_heat and len(numeric_cols) >= 2:
                    try:
                        fig = plt.figure(figsize=(8,6))
                        sns.heatmap(df[numeric_cols].corr(), annot=True, fmt=".2f", cmap="RdPu", center=0)
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        fig.savefig(tmp.name, bbox_inches="tight")
                        plt.close(fig)
                        tmp_files.append(tmp.name)
                        pdf.add_page()
                        add_image_pdf(pdf, tmp.name, x=10, w=190)
                    except Exception:
                        pass

                # Scatter (first pair)
                if include_scatter and len(numeric_cols) >= 2:
                    try:
                        xcol = numeric_cols[0]; ycol = numeric_cols[1]
                        fig = plt.figure(figsize=(6,4))
                        plt.scatter(df[xcol].dropna(), df[ycol].dropna(), alpha=0.6)
                        plt.title(f"{xcol} vs {ycol}")
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                        fig.savefig(tmp.name, bbox_inches="tight")
                        plt.close(fig)
                        tmp_files.append(tmp.name)
                        pdf.add_page()
                        add_image_pdf(pdf, tmp.name, x=15, w=180)
                    except Exception:
                        pass

                # Team list
                pdf.add_page()
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "Team Members", ln=True)
                pdf.set_font("Arial", size=10)
                for m in st.session_state.get("members", []):
                    pdf.multi_cell(0, 6, f"Name: {m.get('name','')} | SID: {m.get('sid','')}")
                    pdf.multi_cell(0, 6, f"Contribution: {shorten(m.get('contrib',''), width=150)}")
                    if m.get("photo_tmp"):
                        try:
                            pdf.image(m["photo_tmp"], x=15, w=40)
                        except Exception:
                            pass
                    pdf.ln(2)

                # cleanup
                for t in tmp_files:
                    try:
                        os.unlink(t)
                    except:
                        pass

                pdf_bytes = pdf.output(dest="S").encode("latin-1")
                st.download_button("Download PDF (Pink Theme)", pdf_bytes, file_name="survey_report_pink.pdf", mime="application/pdf")

# ---------------------------
# PAGE: Team
# ---------------------------
# Initialize session state for members
if "members" not in st.session_state:
    st.session_state["members"] = []
elif page == T["team"]:
    st.header(T["team"])
    with st.form("member_form", clear_on_submit=True):
        name = st.text_input("Name / Nama")
        sid = st.text_input("SID")
        contrib = st.text_area("Contribution / Kontribusi")
        photo = st.file_uploader("Photo (jpg/png)", type=["jpg","jpeg","png"], key="photo")
        submitted = st.form_submit_button("Add Member")
        if submitted:
            photo_tmp = None
            if photo is not None:
                tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tmpf.write(photo.getvalue())
                tmpf.flush()
                photo_tmp = tmpf.name
            st.session_state["members"].append({
                "name": name,
                "sid": sid,
                "contrib": contrib,
                "photo_tmp": photo_tmp
            })
            st.success("Member added")

    # preview & remove
    members = st.session_state.get("members", [])
    if members:
        for idx, m in enumerate(members):
            c1, c2, c3 = st.columns([1,3,1])
            with c1:
                if m.get("photo_tmp"):
                    st.image(m["photo_tmp"], width=80)
            with c2:
                st.markdown(f"**{m.get('name','')}**")
                st.markdown(f"SID: {m.get('sid','')}")
                st.markdown(f"Contribution: {m.get('contrib','')}")
            with c3:
                if st.button(f"Remove {idx}", key=f"rm_{idx}"):
                    try:
                        if m.get("photo_tmp"):
                            os.unlink(m["photo_tmp"])
                    except:
                        pass
                    st.session_state["members"].pop(idx)
                    st.experimental_rerun()

# ---------------------------
# End of file
# ---------------------------
