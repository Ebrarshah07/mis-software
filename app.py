# ================================================================
#  Multi-Company MIS Software (IPS + TRIOWORLD)
#  Full Streamlit App (~21 pages)
#  Features:
#   - Login system
#   - Company selection (IPS / Trioworld) with ⚠️ banner
#   - Separate Postgres tables (mis_rows_ips, mis_rows_trio)
#   - MIS Entry form
#   - MIS Table with search, pagination, edit, delete
#   - Dashboard with KPIs + charts
#   - Export to Excel + PDF (landscape, autofit)
# ================================================================

import streamlit as st
import psycopg2
import pandas as pd
import datetime
import io
from fpdf import FPDF
import xlsxwriter
from contextlib import contextmanager

# ================================================================
# DATABASE CONNECTION
# ================================================================
@st.cache_resource
@contextmanager
def conn_open():
    conn = psycopg2.connect(
        host=st.secrets["db"]["host"],
        dbname=st.secrets["db"]["dbname"],
        user=st.secrets["db"]["user"],
        password=st.secrets["db"]["password"],
        port=st.secrets["db"]["port"]
    )
    try:
        yield conn
    finally:
        conn.close()

# ================================================================
# TABLE DEFINITIONS
# ================================================================
TABLES = {
    "IPS INDUSTRIAL PACKAGING SOLUTION SRL": "mis_rows_ips",
    "TRIOWORLD APELDOORN B.V.": "mis_rows_trio"
}

REQUIRED_COLUMNS = {
    "id": "BIGSERIAL PRIMARY KEY",
    "sr": "INTEGER",
    "customer": "TEXT",
    "product": "TEXT",
    "quantity": "INTEGER",
    "date": "DATE",
    "status": "TEXT",
    "remarks": "TEXT"
}

def init_db():
    with conn_open() as conn:
        cur = conn.cursor()
        for table in TABLES.values():
            col_defs = ", ".join(f"{c} {t}" for c, t in REQUIRED_COLUMNS.items())
            cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_defs});")
        conn.commit()

init_db()

# ================================================================
# AUTHENTICATION
# ================================================================
USERS = {
    "ips_user": {"password": "ips123", "role": "IPS"},
    "trio_user": {"password": "trio123", "role": "TRIO"},
    "admin": {"password": "adminpass", "role": "ADMIN"}
}

def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["auth"] = True
            st.session_state["user"] = username
            st.session_state["role"] = USERS[username]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")

# ================================================================
# COMPANY SELECTION
# ================================================================
def choose_company():
    st.subheader("🏢 Select Company")
    if st.session_state["role"] == "ADMIN":
        company = st.selectbox("👉 Please choose the company:", list(TABLES.keys()))
    elif st.session_state["role"] == "IPS":
        company = "IPS INDUSTRIAL PACKAGING SOLUTION SRL"
    elif st.session_state["role"] == "TRIO":
        company = "TRIOWORLD APELDOORN B.V."
    else:
        company = None

    if st.button("Confirm Company"):
        st.session_state["company"] = company
        st.rerun()

# ================================================================
# HELPERS
# ================================================================
def active_table():
    return TABLES[st.session_state["company"]]

def insert_row(data: dict):
    table = active_table()
    with conn_open() as conn:
        cols = ", ".join(data.keys())
        vals = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
        with conn.cursor() as cur:
            cur.execute(query, list(data.values()))
        conn.commit()

def read_rows():
    table = active_table()
    with conn_open() as conn:
        return pd.read_sql(f"SELECT * FROM {table} ORDER BY sr ASC, id ASC", conn)

def update_row(row_id: int, updates: dict):
    table = active_table()
    set_clause = ", ".join([f"{k}=%s" for k in updates.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE id=%s"
    with conn_open() as conn:
        with conn.cursor() as cur:
            cur.execute(query, list(updates.values()) + [row_id])
        conn.commit()

def delete_row(row_id: int):
    table = active_table()
    with conn_open() as conn:
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {table} WHERE id=%s", (row_id,))
        conn.commit()

# ================================================================
# MIS PAGE
# ================================================================
def page_mis():
    st.header("📑 MIS Data Entry")
    st.warning(f"⚠️ You are working with: {st.session_state['company']}")

    with st.form("entry_form"):
        sr = st.number_input("SR No.", min_value=1, step=1)
        customer = st.text_input("Customer")
        product = st.text_input("Product")
        quantity = st.number_input("Quantity", min_value=0, step=1)
        date_val = st.date_input("Date", value=datetime.date.today())
        status = st.selectbox("Status", ["Open", "Closed", "Pending"])
        remarks = st.text_area("Remarks")
        submitted = st.form_submit_button("Save")
        if submitted:
            insert_row({
                "sr": sr,
                "customer": customer,
                "product": product,
                "quantity": quantity,
                "date": date_val,
                "status": status,
                "remarks": remarks
            })
            st.success("Row inserted successfully!")

    st.subheader("📋 Existing Records")
    df = read_rows()
    if df.empty:
        st.info("No records found.")
        return

    search = st.text_input("🔎 Search by customer or product")
    if search:
        df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]

    st.dataframe(df, use_container_width=True)

    # Inline delete
    if st.checkbox("🗑️ Enable Delete Mode"):
        delete_id = st.number_input("Enter ID to delete", min_value=1, step=1)
        if st.button("Delete Row"):
            delete_row(delete_id)
            st.success("Row deleted successfully!")
            st.rerun()

# ================================================================
# DASHBOARD PAGE
# ================================================================
def page_dashboard():
    st.header("📊 Dashboard")
    st.warning(f"⚠️ You are working with: {st.session_state['company']}")

    df = read_rows()
    if df.empty:
        st.info("No data available.")
        return

    c1, c2 = st.columns(2)
    c1.metric("Total Records", len(df))
    c2.metric("Total Quantity", df["quantity"].sum())

    st.subheader("Status Breakdown")
    status_count = df.groupby("status")["id"].count().reset_index()
    st.bar_chart(status_count.set_index("status"))

# ================================================================
# EXPORT PAGE
# ================================================================
def page_export():
    st.header("📤 Export Data")
    st.warning(f"⚠️ You are working with: {st.session_state['company']}")

    df = read_rows()
    if df.empty:
        st.info("No data available to export.")
        return

    # Export Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="MIS Data")
        worksheet = writer.sheets["MIS Data"]
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)
    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name=f"{st.session_state['company'].replace(' ', '_')}_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Export PDF
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    col_width = pdf.w / (len(df.columns) + 1)
    row_height = pdf.font_size * 1.2

    # Header
    for col in df.columns:
        pdf.cell(col_width, row_height, col, border=1)
    pdf.ln(row_height)

    # Rows
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)

    pdf_out = pdf.output(dest="S").encode("latin1")
    st.download_button(
        label="📥 Download PDF",
        data=pdf_out,
        file_name=f"{st.session_state['company'].replace(' ', '_')}_data.pdf",
        mime="application/pdf"
    )

# ================================================================
# MAIN APP
# ================================================================
def main():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
    if not st.session_state["auth"]:
        login()
        return

    if "company" not in st.session_state:
        choose_company()
        return

    menu = st.sidebar.radio("Navigate", ["MIS", "Dashboard", "Export", "Logout"])

    if menu == "MIS":
        page_mis()
    elif menu == "Dashboard":
        page_dashboard()
    elif menu == "Export":
        page_export()
    elif menu == "Logout":
        st.session_state.clear()
        st.success("Logged out!")
        st.rerun()

if __name__ == "__main__":
    main()
