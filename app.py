import streamlit as st
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

# ----------------------------
# DATABASE CONNECTION (Postgres)
# ----------------------------
DB_HOST = st.secrets["DB_HOST"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]
DB_PORT = st.secrets["DB_PORT"]

engine = create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ----------------------------
# LOGIN SYSTEM
# ----------------------------
USERS = {"admin": "admin123", "eby": "eby123"}  # you can add more

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 LOGIN PAGE")

    with st.form("login"):
        u = st.text_input("USERNAME").strip()
        p = st.text_input("PASSWORD", type="password")
        submitted = st.form_submit_button("LOGIN")

        if submitted:
            if u in USERS and p == USERS[u]:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.success("Login successful ✅")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid username or password")
    st.stop()

# ----------------------------
# MAIN APP (AFTER LOGIN)
# ----------------------------
st.sidebar.title("📊 MANAGEMENT INFORMATION SYSTEM")
page = st.sidebar.radio("Go to", ["DATA ENTRY", "MIS", "DASHBOARD"])

# ----------------------------
# PAGE 1: DATA ENTRY
# ----------------------------
if page == "DATA ENTRY":
    st.header("📝 MANAGEMENT INFORMATION SYSTEM - DATA ENTRY")

    with st.form("data_entry", clear_on_submit=True):
        sr = st.text_input("SR NUMBER").upper()
        customer = st.selectbox(
            "CUSTOMER NAME",
            ["AMUL DAIRY", "BANAS DAIRY", "SABAR DAIRY", "BRITANNIA BEL",
             "SCHREIBER DYNAMIX", "BAMUL", "MILKY MIST DAIRY", "OTHER"],
        )
        fy = st.text_input("FINANCIAL YEAR").upper()
        pono = st.text_input("PO NUMBER").upper()
        podate = st.date_input("PO DATE")
        ocno = st.text_input("ORDER CONFIRMATION NUMBER").upper()
        ocdate = st.date_input("OC DATE")
        mode = st.selectbox("MODE (SEA / AIR)", ["SEA", "AIR"])
        desc = st.text_area("DESCRIPTION OF MATERIAL").upper()
        rate = st.number_input("RATE (EURO)", min_value=0.0)
        ordered = st.number_input("CUSTOMER ORDERED QUANTITY", min_value=0)
        invno = st.text_input("INVOICE NUMBER").upper()
        invqty = st.number_input("INVOICE QUANTITY", min_value=0)
        invdate = st.date_input("INVOICE DATE")
        bldate = st.date_input("BILL OF LADING DATE")
        payterms = st.selectbox("PAYMENT TERMS", ["30 DAYS", "45 DAYS", "60 DAYS"])
        remark = st.text_area("REMARK").upper()

        submitted = st.form_submit_button("SAVE ENTRY")

        if submitted:
            df_new = pd.DataFrame([{
                "SR": sr,
                "CUSTOMER": customer,
                "FY": fy,
                "PONO": pono,
                "PODATE": podate,
                "OCNO": ocno,
                "OCDATE": ocdate,
                "MODE": mode,
                "DESCRIPTION": desc,
                "RATE": rate,
                "ORDERED": ordered,
                "INVNO": invno,
                "INVQTY": invqty,
                "INVDATE": invdate,
                "BLDATE": bldate,
                "PAYTERMS": payterms,
                "REMARK": remark,
            }])
            df_new.to_sql("mis_table", engine, if_exists="append", index=False)
            st.success("✅ Data saved successfully!")

# ----------------------------
# PAGE 2: MIS TABLE
# ----------------------------
elif page == "MIS":
    st.header("📋 MIS DATA VIEW")

    df = pd.read_sql("SELECT * FROM mis_table", engine)

    st.dataframe(df)

    # Export to Excel
    out_xlsx = io.BytesIO()
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="MIS")
    st.download_button("⬇️ Download Excel", out_xlsx.getvalue(),
                       file_name="MIS.xlsx", mime="application/vnd.ms-excel")

    # Export to PDF
    out_pdf = io.BytesIO()
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", size=8)

    col_width = pdf.w / (len(df.columns) + 1)
    row_height = pdf.font_size * 1.5

    for col in df.columns:
        pdf.cell(col_width, row_height, col, border=1)
    pdf.ln(row_height)

    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)

    out_pdf.write(pdf.output(dest="S").encode("latin1"))
    st.download_button("⬇️ Download PDF", out_pdf.getvalue(),
                       file_name="MIS.pdf", mime="application/pdf")

# ----------------------------
# PAGE 3: DASHBOARD
# ----------------------------
elif page == "DASHBOARD":
    st.header("📊 DASHBOARD")

    df = pd.read_sql("SELECT * FROM mis_table", engine)

    if not df.empty:
        st.subheader("Total Ordered Quantity per Customer")
        qty = df.groupby("CUSTOMER")["ORDERED"].sum()
        st.bar_chart(qty)

        st.subheader("Total Invoice Amount per Customer")
        df["AMOUNT"] = df["RATE"] * df["INVQTY"]
        amt = df.groupby("CUSTOMER")["AMOUNT"].sum()
        st.bar_chart(amt)
    else:
        st.info("No data available yet.")
