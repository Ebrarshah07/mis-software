import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection from secrets
DB = st.secrets["db"]  # reads the values you saved in secrets
engine = create_engine(
    f"postgresql+psycopg2://{DB['user']}:{DB['password']}@{DB['host']}:{DB['port']}/{DB['name']}?sslmode=require",
    pool_pre_ping=True,
)

# app.py
# ------------------------------------------------------------
# MANAGEMENT INFORMATION SYSTEM (Streamlit + SQLite)
# - Same UI/flow as before
# - Fixed Landscape PDF export (no overlap, wrapped text, auto-fit)
# - Excel export (openpyxl/xlsxwriter)
# ------------------------------------------------------------

from datetime import datetime, timedelta, date
from io import BytesIO
import pandas as pd
import streamlit as st

# ===== Optional PDF dependency (safe fallback if not installed) =====
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.pdfbase.pdfmetrics import stringWidth
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

# ===================== APP CONFIG =====================
st.set_page_config(page_title="MANAGEMENT INFORMATION SYSTEM", layout="wide")

# ----------- AUTH (MULTI-USER LOGIN) -----------
USERS = {
    "admin":   "Admin@123",
    "manager": "Manager@123",
    "viewer":  "Viewer@123",
}

def require_login():
    if "auth" not in st.session_state:
        st.session_state["auth"] = False
        st.session_state["user"] = None

    if not st.session_state["auth"]:
        # Centered login using 3 columns
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.title("🔐 LOGIN")
            u = st.text_input("USERNAME").strip()
            p = st.text_input("PASSWORD", type="password")
            bcol1, bcol2, _ = st.columns([1, 3, 1])
            if bcol1.button("LOGIN"):
                if u in USERS and p == USERS[u]:
                    st.session_state["auth"] = True
                    st.session_state["user"] = u
                    st.success("LOGIN SUCCESS ✅")
                    st.rerun()
                else:
                    st.error("INVALID CREDENTIALS")
        st.stop()

require_login()

# Top bar: user + logout
top_left, top_mid, top_right = st.columns([2,6,2])
with top_left:
    st.caption(f"LOGGED IN AS: **{st.session_state['user'].upper()}**")
with top_right:
    if st.button("LOGOUT"):
        st.session_state["auth"] = False
        st.session_state["user"] = None
        st.rerun()

# ===================== UTILITIES =====================
YESNO = ["YES", "NO"]
CUSTOMERS = [
    "AMUL DAIRY", "BANAS DAIRY", "SABAR DAIRY", "BRITANNIA BEL",
    "SCHREIBER DYNAMIX", "BAMUL", "MILKY MIST DAIRY", "OTHER (TYPE MANUALLY)"
]
FY_DEFAULTS = ["2023-2024", "2024-2025", "2025-2026", "TYPE MANUALLY"]

def to_caps(x):
    if x is None: return ""
    return str(x).upper()

def fmt_date(d):
    return d.strftime("%Y-%m-%d") if isinstance(d, (datetime, date)) else (str(d) if d else "")

def calc_due(bl_str, days):
    if not bl_str or not days: return ""
    try:
        d = datetime.strptime(bl_str, "%Y-%m-%d")
        return (d + timedelta(days=int(days))).strftime("%Y-%m-%d")
    except Exception:
        return ""

def is_overdue(duedate_str, paystatus):
    try:
        if to_caps(paystatus) == "YES":
            return False
        if not duedate_str:
            return False
        dd = datetime.strptime(duedate_str, "%Y-%m-%d").date()
        return date.today() > dd
    except Exception:
        return False

# ===================== DATABASE =====================
from sqlalchemy import create_engine, text
import pandas as pd

# Supabase connection details
DB_HOST = "aws-1-ap-south-1.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.jupxcnjnffatpcyhoowb"
DB_PASS = "ebrarpyloff123@"

# Create SQLAlchemy engine
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Initialize DB (create table if not exists)
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mis_data (
                id SERIAL PRIMARY KEY,
                sr INT,
                customer TEXT,
                fy TEXT,
                pono TEXT,
                podate TEXT,
                ocno TEXT,
                ocdate TEXT,
                mode TEXT,
                description TEXT,
                rate FLOAT,
                ordered FLOAT,
                invno TEXT,
                invqty FLOAT,
                invdate TEXT,
                bldate TEXT,
                payterms INT,
                duedate TEXT,
                paystatus TEXT,
                scadenza TEXT,
                remark TEXT,
                invoice_shared TEXT,
                packing_shared TEXT,
                coa_shared TEXT,
                hd_shared TEXT,
                coo_shared TEXT,
                insurance_shared TEXT,
                created_at TEXT
            )
        """))

# Insert row
def insert_row(data: dict):
    cols = ",".join(data.keys())
    vals = ",".join([f":{k}" for k in data.keys()])
    query = text(f"INSERT INTO mis_data ({cols}) VALUES ({vals})")
    with engine.begin() as conn:
        conn.execute(query, data)

# Update row
def update_row(row_id: int, data: dict):
    set_clause = ",".join([f"{k}=:{k}" for k in data.keys()])
    query = text(f"UPDATE mis_data SET {set_clause} WHERE id=:id")
    data["id"] = row_id
    with engine.begin() as conn:
        conn.execute(query, data)

# Read rows into DataFrame
def read_rows() -> pd.DataFrame:
    query = text("SELECT * FROM mis_data ORDER BY id ASC")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

# Create SQLAlchemy engine
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Initialize DB (create table if not exists)
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mis_data (
                id SERIAL PRIMARY KEY,
                sr INT,
                customer TEXT,
                fy TEXT,
                pono TEXT,
                podate TEXT,
                ocno TEXT,
                ocdate TEXT,
                mode TEXT,
                description TEXT,
                rate FLOAT,
                ordered FLOAT,
                invno TEXT,
                invqty FLOAT,
                invdate TEXT,
                bldate TEXT,
                payterms INT,
                duedate TEXT,
                paystatus TEXT,
                scadenza TEXT,
                remark TEXT,
                invoice_shared TEXT,
                packing_shared TEXT,
                coa_shared TEXT,
                hd_shared TEXT,
                coo_shared TEXT,
                insurance_shared TEXT,
                created_at TEXT
            )
        """))

# Insert row
def insert_row(data: dict):
    cols = ",".join(data.keys())
    vals = ",".join([f":{k}" for k in data.keys()])
    query = text(f"INSERT INTO mis_data ({cols}) VALUES ({vals})")
    with engine.begin() as conn:
        conn.execute(query, data)

# Update row
def update_row(row_id: int, data: dict):
    set_clause = ",".join([f"{k}=:{k}" for k in data.keys()])
    query = text(f"UPDATE mis_data SET {set_clause} WHERE id=:id")
    data["id"] = row_id
    with engine.begin() as conn:
        conn.execute(query, data)

# Read rows into DataFrame
def read_rows() -> pd.DataFrame:
    query = text("SELECT * FROM mis_data ORDER BY id ASC")
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df



# ===================== STYLES =====================
st.markdown("""
<style>
/* ALL CAPS VISUAL */
h1,h2,h3,h4,h5,h6, label, th, [data-testid="stMetricLabel"], .stMarkdown p { text-transform: uppercase; }

/* compact container */
.block-container { padding-top: 0.8rem; padding-bottom: 0.8rem; }

/* MIS TABLE styles */
.table-wrap { overflow: auto; border-radius: 10px; border: 1px solid #e5e7eb; }
table.mis-table { border-collapse: separate; border-spacing: 0; width: 100%; font-size: 0.92rem; }
table.mis-table th, table.mis-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; white-space: nowrap; }
table.mis-table th { position: sticky; top: 0; background: #0ea5e9; color: white; z-index: 3; }
table.mis-table td.sticky, table.mis-table th.sticky { position: sticky; left: 0; background: #f8fafc; z-index: 2; }
tr.air-row td { background: #fff7cc !important; } /* AIR = yellow */

/* badges */
.badge-yes { background: #dcfce7; color:#166534; padding:2px 8px; border-radius:999px; font-weight:800; border:1px solid #16a34a33;}
.badge-no  { background: #fee2e2; color:#991b1b; padding:2px 8px; border-radius:999px; font-weight:800; border:1px solid #ef444433;}
.badge-overdue { background:#ffe4e6; color:#b91c1c; padding:2px 8px; border-radius:999px; font-weight:800; border:1px solid #ef4444aa; }

/* blinking banner */
@keyframes blink { 50% { opacity: 0.25; } }
.blink { animation: blink 1s step-start 0s infinite; }
</style>
""", unsafe_allow_html=True)

# ===================== NAV =====================
page = st.sidebar.radio("SELECT PAGE", ["MANAGEMENT INFORMATION SYSTEM", "MIS", "DASHBOARD"])

# Initialize dynamic item rows
if "items" not in st.session_state:
    st.session_state["items"] = [
        dict(desc="", rate=0.0, qty=0.0, invno="", invqty=0.0,
             invdate=date.today(), bldate=date.today(), payterms=30,
             duedate="", paystatus="NO", remark="",
             invoice_shared="NO", packing_shared="NO", coa_shared="NO",
             hd_shared="NO", coo_shared="NO", insurance_shared="NO")
    ]

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# ===================== PDF HELPERS (Landscape + Wrapping + Auto-Fit) =====================
def build_table_data_upper(df: pd.DataFrame):
    df_str = df.copy()
    for c in df_str.columns:
        df_str[c] = df_str[c].astype(str).fillna("").str.upper()
    data = [list(df_str.columns)] + df_str.values.tolist()
    return data

def _as_paragraphs(data, body_style, header_style):
    """Convert each cell to a Paragraph to enable wrapping (no overlap)."""
    new = []
    for r, row in enumerate(data):
        out = []
        for c in row:
            text = "" if c is None else str(c)
            if r == 0:
                out.append(Paragraph(text, header_style))
            else:
                out.append(Paragraph(text, body_style))
        new.append(out)
    return new

def df_to_pdf_bytes_landscape_autofit(title, df, base_font=9.5, min_font=6.0, header_font=9.5):
    """
    Create a readable A4-Landscape PDF for wide MIS table:
      - Word-wrapped headers and cells (Paragraph)
      - Iteratively reduces font until table fits page width
      - Subtle row striping, sticky-style repeated header
    """
    if not REPORTLAB_OK:
        return None

    buf = BytesIO()
    pagesize = landscape(A4)
    doc = SimpleDocTemplate(
        buf, pagesize=pagesize,
        leftMargin=18, rightMargin=18, topMargin=24, bottomMargin=24
    )
    styles = getSampleStyleSheet()

    # Paragraph styles (we’ll change font size on the fly)
    body_style = ParagraphStyle(
        "BodyCell", parent=styles["Normal"],
        fontName="Helvetica", fontSize=base_font, leading=base_font + 1,
        spaceAfter=0, spaceBefore=0
    )
    header_style = ParagraphStyle(
        "HeadCell", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=header_font, leading=header_font + 1,
        textColor=colors.white
    )

    raw = build_table_data_upper(df)
    col_count = len(raw[0])

    # Compute target widths by measuring the longest string in each column
    # (we measure at current font; we will try smaller fonts if needed)
    def measure_widths(font_size):
        body_style.fontSize = font_size
        body_style.leading = font_size + 1
        padd = 8  # inner padding per cell side
        widths = []
        for col_idx in range(col_count):
            # Longest text among header+cells
            items = [str(r[col_idx]) for r in raw]
            longest = max(items, key=len) if items else ""
            # Reserve more width for a few known wide columns
            bonus = 1.25 if any(k in raw[0][col_idx].upper() for k in ["DESCRIPTION", "CUSTOMER", "REMARK"]) else 1.0
            w = stringWidth(longest, "Helvetica", font_size) * bonus + padd * 2
            # clamp min/max
            w = max(42, min(w, 260))
            widths.append(w)
        return sum(widths), widths

    avail = pagesize[0] - doc.leftMargin - doc.rightMargin
    font = base_font
    widths = None
    # Try to fit width by reducing font size
    while font >= min_font:
        total, w_try = measure_widths(font)
        if total <= avail:
            widths = w_try
            break
        font -= 0.5

    if widths is None:  # still too wide: force equal widths at minimum font
        widths = [avail / col_count] * col_count
        font = min_font

    # Update body/header sizes with final font
    body_style.fontSize = font
    body_style.leading = font + 1
    header_style.fontSize = min(max(font, 8.0), header_font)  # keep header readable
    header_style.leading = header_style.fontSize + 1

    # Wrap all cells with Paragraph so content NEVER overlaps
    data_wrapped = _as_paragraphs(raw, body_style, header_style)

    elems = [Paragraph(to_caps(title), styles["Title"]), Spacer(1, 6)]
    table = Table(data_wrapped, colWidths=widths, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.HexColor("#f8fafc")]),
        # Tighter padding to maximize room (also prevents visual overlap)
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        # Enable wrapping at the Table level too
        ("WORDWRAP", (0,0), (-1,-1), "CJK"),
    ]))
    elems.append(table)
    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()

def dashboard_to_pdf_bytes_landscape(title, tables: list):
    """Landscape dashboard PDF (each table auto-fit with wrapping)."""
    if not REPORTLAB_OK:
        return None

    buf = BytesIO()
    pagesize = landscape(A4)
    doc = SimpleDocTemplate(buf, pagesize=pagesize, leftMargin=18, rightMargin=18, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    elems = [Paragraph(to_caps(title), styles["Title"]), Spacer(1, 6)]

    for subtitle, df in tables:
        elems.append(Paragraph(to_caps(subtitle), styles["Heading3"]))

        raw = build_table_data_upper(df)
        if not raw or not raw[0]:
            continue
        col_count = len(raw[0])
        body_style = ParagraphStyle("BodyDash", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=10)
        head_style = ParagraphStyle("HeadDash", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=10, textColor=colors.white)

        def measure(font_size):
            padd = 8
            widths = []
            for c in range(col_count):
                items = [str(r[c]) for r in raw]
                longest = max(items, key=len) if items else ""
                bonus = 1.2 if any(k in raw[0][c].upper() for k in ["CUSTOMER","DESCRIPTION"]) else 1.0
                w = stringWidth(longest, "Helvetica", font_size) * bonus + padd*2
                w = max(42, min(w, 260))
                widths.append(w)
            return sum(widths), widths

        avail = pagesize[0] - doc.leftMargin - doc.rightMargin
        f = 9.0
        widths = None
        while f >= 6.0:
            tot, w_try = measure(f)
            if tot <= avail:
                widths = w_try
                break
            f -= 0.5
        if widths is None:
            widths = [avail/col_count]*col_count
            f = 6.0

        body_style.fontSize = f
        body_style.leading = f + 1
        head_style.fontSize = max(f, 8.0)
        head_style.leading = head_style.fontSize + 1

        wrapped = _as_paragraphs(raw, body_style, head_style)
        t = Table(wrapped, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0ea5e9")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.HexColor("#f8fafc")]),
            ("LEFTPADDING", (0,0), (-1,-1), 3),
            ("RIGHTPADDING", (0,0), (-1,-1), 3),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("WORDWRAP", (0,0), (-1,-1), "CJK"),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 8))

    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()

# ===================== PAGE 1: MANAGEMENT INFORMATION SYSTEM =====================
if page == "MANAGEMENT INFORMATION SYSTEM":
    st.header("MANAGEMENT INFORMATION SYSTEM")

    with st.form("mis_form", clear_on_submit=False):
        # top section
        L, R = st.columns(2, gap="large")

        with L:
            sr = st.number_input("SR NUMBER", min_value=1, step=1)
            cust_sel = st.selectbox("CUSTOMER NAME", options=CUSTOMERS, index=1)
            if "OTHER" in cust_sel:
                customer = st.text_input("CUSTOMER NAME (TYPE)").upper()
            else:
                customer = cust_sel

            fy_sel = st.selectbox("FINANCIAL YEAR", options=FY_DEFAULTS, index=1)
            fy = st.text_input("FINANCIAL YEAR (MANUAL)").upper() if fy_sel == "TYPE MANUALLY" else fy_sel

            mode = st.selectbox("MODE (SEA / AIR)", options=["SEA", "AIR"], index=0)

        with R:
            pono = st.text_input("PO NUMBER").upper()
            podate = st.date_input("PO DATE", format="YYYY-MM-DD")
            ocno = st.text_input("OC NUMBER").upper()
            ocdate = st.date_input("OC DATE", format="YYYY-MM-DD")
            scadenza = st.date_input("SCADENZA / SCHEDULE DATE", format="YYYY-MM-DD")

        if mode == "AIR":
            st.markdown('<div style="height:8px;background:#fff7cc;border:1px solid #fde68a;"></div>', unsafe_allow_html=True)

        st.markdown("### ITEMS (ADD LINES AS NEEDED)")

        new_items = []
        for i, item in enumerate(st.session_state["items"]):
            c1, c2, c3, c4, c5, c6 = st.columns([3,1.2,1.2,1.8,1.8,1.6])

            desc = c1.text_input(f"DESCRIPTION #{i+1}", value=item["desc"], key=f"desc_{i}").upper()
            rate = c2.number_input(f"RATE (EURO) #{i+1}", value=float(item["rate"]), step=0.01, key=f"rate_{i}")
            qty  = c3.number_input(f"ORDER QTY #{i+1}", value=float(item["qty"]), step=1.0, key=f"qty_{i}")
            invno = c4.text_input(f"INVOICE NO #{i+1}", value=item["invno"], key=f"invno_{i}").upper()
            invqty = c5.number_input(f"INVOICE QTY #{i+1}", value=float(item["invqty"]), step=1.0, key=f"invqty_{i}")
            invdate = c6.date_input(f"INVOICE DATE #{i+1}", value=item["invdate"], format="YYYY-MM-DD", key=f"invdate_{i}")

            d1, d2, d3, d4 = st.columns([1.6,1,1.6,1.6])
            bldate = d1.date_input(f"BL DATE #{i+1}", value=item["bldate"], format="YYYY-MM-DD", key=f"bldate_{i}")
            payterms = d2.selectbox(f"TERMS (DAYS) #{i+1}", options=[30,45,60],
                                    index=[30,45,60].index(int(item["payterms"])) if item["payterms"] in [30,45,60] else 0,
                                    key=f"terms_{i}")
            due = calc_due(fmt_date(bldate), payterms)
            d3.write(f"**DUE DATE:** {due or '-'}")
            paystatus = d4.selectbox(f"PAYMENT STATUS #{i+1}", options=YESNO,
                                     index=1 if item["paystatus"]=="NO" else 0, key=f"paystat_{i}")

            # Document flags
            f1, f2, f3, f4, f5, f6 = st.columns(6)
            invoice_shared = f1.selectbox(f"INVOICE SHARED #{i+1}", YESNO, index=YESNO.index(item.get("invoice_shared","NO")), key=f"invshared_{i}")
            packing_shared = f2.selectbox(f"PACKING LIST SHARED #{i+1}", YESNO, index=YESNO.index(item.get("packing_shared","NO")), key=f"packshared_{i}")
            coa_shared     = f3.selectbox(f"COA SHARED #{i+1}", YESNO, index=YESNO.index(item.get("coa_shared","NO")), key=f"coashared_{i}")
            hd_shared      = f4.selectbox(f"HD SHARED #{i+1}", YESNO, index=YESNO.index(item.get("hd_shared","NO")), key=f"hdshared_{i}")
            coo_shared     = f5.selectbox(f"COO SHARED #{i+1}", YESNO, index=YESNO.index(item.get("coo_shared","NO")), key=f"cooshared_{i}")
            insurance_shared = f6.selectbox(f"INSURANCE SHARED #{i+1}", YESNO, index=YESNO.index(item.get("insurance_shared","NO")), key=f"insshared_{i}")

            remark = st.text_input(f"REMARK #{i+1}", value=item["remark"], key=f"rem_{i}").upper()

            new_items.append(dict(
                desc=desc, rate=rate, qty=qty, invno=invno, invqty=invqty,
                invdate=invdate, bldate=bldate, payterms=payterms,
                duedate=due, paystatus=paystatus, remark=remark,
                invoice_shared=invoice_shared, packing_shared=packing_shared,
                coa_shared=coa_shared, hd_shared=hd_shared,
                coo_shared=coo_shared, insurance_shared=insurance_shared
            ))

        st.session_state["items"] = new_items

        col_a, col_b = st.columns(2)
        add_clicked = col_a.form_submit_button("➕ ADD ITEM ROW")
        save_clicked = col_b.form_submit_button("💾 SAVE")

        if add_clicked:
            st.session_state["items"].append(
                dict(desc="", rate=0.0, qty=0.0, invno="", invqty=0.0,
                     invdate=date.today(), bldate=date.today(), payterms=30,
                     duedate="", paystatus="NO", remark="",
                     invoice_shared="NO", packing_shared="NO", coa_shared="NO",
                     hd_shared="NO", coo_shared="NO", insurance_shared="NO")
            )
            safe_rerun()

        if save_clicked:
            base = dict(
                sr=int(sr),
                customer=to_caps(customer),
                fy=to_caps(fy),
                pono=to_caps(pono),
                podate=fmt_date(podate),
                ocno=to_caps(ocno),
                ocdate=fmt_date(ocdate),
                mode=to_caps(mode),
                scadenza=fmt_date(scadenza),
                created_at=datetime.utcnow().isoformat()
            )
            for it in st.session_state["items"]:
                row = base | dict(
                    description=to_caps(it["desc"]),
                    rate=float(it["rate"] or 0),
                    ordered=float(it["qty"] or 0),
                    invno=to_caps(it["invno"]),
                    invqty=float(it["invqty"] or 0),
                    invdate=fmt_date(it["invdate"]),
                    bldate=fmt_date(it["bldate"]),
                    payterms=int(it["payterms"] or 0),
                    duedate=to_caps(it["duedate"]),
                    paystatus=to_caps(it["paystatus"]),
                    remark=to_caps(it["remark"]),
                    invoice_shared=to_caps(it["invoice_shared"]),
                    packing_shared=to_caps(it["packing_shared"]),
                    coa_shared=to_caps(it["coa_shared"]),
                    hd_shared=to_caps(it["hd_shared"]),
                    coo_shared=to_caps(it["coo_shared"]),
                    insurance_shared=to_caps(it["insurance_shared"])
                )
                insert_row(row)
            st.success("✅ SAVED. OPEN ‘MIS’ PAGE TO VIEW ALL ROWS.")

# ===================== PAGE 2: MIS (TABLE + SEARCH + EXPORTS + EDIT) =====================
elif page == "MIS":
    st.header("MIS")
    df = read_rows()

    if df.empty:
        st.info("NO DATA YET")
    else:
        # SEARCH
        c1, c2, c3 = st.columns([2,2,2])
        with c1: po_q = to_caps(st.text_input("SEARCH BY PO NUMBER"))
        with c2: oc_q = to_caps(st.text_input("SEARCH BY OC NUMBER"))
        with c3: cu_q = to_caps(st.text_input("SEARCH BY CUSTOMER"))

        if po_q: df = df[df["pono"].astype(str).str.upper().str.contains(po_q, na=False)]
        if oc_q: df = df[df["ocno"].astype(str).str.upper().str.contains(oc_q, na=False)]
        if cu_q: df = df[df["customer"].astype(str).str.upper().str.contains(cu_q, na=False)]

        # Uppercase strings for display
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].fillna("").astype(str).str.upper()

        # Add OVERDUE column
        df["OVERDUE"] = df.apply(lambda r: "YES" if is_overdue(r.get("duedate",""), r.get("paystatus","NO")) else "NO", axis=1)

        # Rename & order for display
        show = df.rename(columns={
            "sr":"SR NUMBER",
            "customer":"CUSTOMER",
            "fy":"FY",
            "pono":"PO NO",
            "podate":"PO DATE",
            "ocno":"OC NO",
            "ocdate":"OC DATE",
            "mode":"MODE",
            "description":"DESCRIPTION",
            "rate":"RATE (EURO)",
            "ordered":"ORDER QUANTITY",
            "invno":"INVOICE NO",
            "invqty":"INVOICE QUANTITY",
            "invdate":"INVOICE DATE",
            "bldate":"BL DATE",
            "payterms":"PAYMENT TERMS",
            "duedate":"DUE DATE",
            "scadenza":"SCADENZA (SCHEDULE DATE)",
            "paystatus":"PAYMENT STATUS",
            "remark":"REMARK",
            "invoice_shared":"INVOICE SHARED",
            "packing_shared":"PACKING LIST SHARED",
            "coa_shared":"COA SHARED",
            "hd_shared":"HD SHARED",
            "coo_shared":"COO SHARED",
            "insurance_shared":"INSURANCE SHARED",
            "OVERDUE":"OVERDUE",
            "id":"ID"
        })

        cols = [
            "SR NUMBER","CUSTOMER","FY","PO NO","PO DATE","OC NO","OC DATE","MODE",
            "DESCRIPTION","RATE (EURO)","ORDER QUANTITY","INVOICE NO","INVOICE QUANTITY",
            "INVOICE DATE","BL DATE","PAYMENT TERMS","DUE DATE","SCADENZA (SCHEDULE DATE)",
            "PAYMENT STATUS","INVOICE SHARED","PACKING LIST SHARED","COA SHARED","HD SHARED",
            "COO SHARED","INSURANCE SHARED","REMARK","OVERDUE","ID"
        ]
        cols = [c for c in cols if c in show.columns]
        show = show[cols]

        # Custom HTML table
        def td(v): return "" if pd.isna(v) else str(v)
        html = ['<div class="table-wrap"><table class="mis-table">']
        html.append("<tr>")
        for h in cols:
            sticky = " sticky" if h == "CUSTOMER" else ""
            html.append(f'<th class="{sticky}">{h}</th>')
        html.append("</tr>")
        for _, r in show.iterrows():
            row_class = "air-row" if td(r.get("MODE","")) == "AIR" else ""
            html.append(f'<tr class="{row_class}">')
            for h in cols:
                v = td(r[h])
                if h in ("PAYMENT STATUS","INVOICE SHARED","PACKING LIST SHARED","COA SHARED","HD SHARED","COO SHARED","INSURANCE SHARED"):
                    v = f'<span class="badge-yes">YES</span>' if v == "YES" else f'<span class="badge-no">NO</span>'
                if h == "OVERDUE" and v == "YES":
                    v = '<span class="badge-overdue blink">OVERDUE</span>'
                sticky = " sticky" if h == "CUSTOMER" else ""
                html.append(f'<td class="{sticky}">{v}</td>')
            html.append("</tr>")
        html.append("</table></div>")
        st.markdown("\n".join(html), unsafe_allow_html=True)

        # Totals + Actions
        tot_inv = pd.to_numeric(df.get("invqty", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        st.caption(f"TOTAL ROWS: {len(df)}   |   TOTAL INVOICE QUANTITY: {int(tot_inv):,}")

        # ===== EXPORTS =====
        exp_left, exp_mid, exp_right = st.columns([1.2,1.2,6])

        # Excel export (filtered) with safe engine
        with exp_left:
            out = BytesIO()
            file_date = datetime.today().strftime("%Y-%m-%d")
            try:
                with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
                    show.to_excel(writer, index=False, sheet_name="MIS")
                    ws = writer.sheets["MIS"]
                    for i, col in enumerate(show.columns):
                        width = min(40, max(12, show[col].astype(str).map(len).max() + 2))
                        ws.set_column(i, i, width)
            except Exception:
                with pd.ExcelWriter(out, engine="openpyxl") as writer:
                    show.to_excel(writer, index=False, sheet_name="MIS")
            out.seek(0)
            st.download_button(
                label="⬇ DOWNLOAD EXCEL",
                data=out.getvalue(),
                file_name=f"MIS_REPORT_{file_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # PDF export (filtered) with LANDSCAPE + WRAP + AUTOFIT (this is the fix)
        with exp_mid:
            if REPORTLAB_OK:
                pdf_bytes = df_to_pdf_bytes_landscape_autofit(
                    "MIS TABLE (FILTERED)", show, base_font=9.5, min_font=6.0, header_font=9.5
                )
                st.download_button(
                    label="⬇ DOWNLOAD PDF",
                    data=pdf_bytes,
                    file_name=f"MIS_REPORT_{file_date}.pdf",
                    mime="application/pdf",
                )
            else:
                st.info("FOR PDF EXPORT: RUN `pip install reportlab`")

        # Delete + Edit
        with exp_right:
            st.write("")
            st.write("")

            # ---- Delete ----
            del_id = st.number_input("DELETE BY ID", min_value=0, step=1, value=0)
            if st.button("🗑️ DELETE ROW"):
                if del_id > 0:
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM mis_data WHERE id=:id"), {"id": int(del_id)})
                st.success("ROW DELETED ✅")
                st.rerun()


            st.divider()

            # ---- Edit Panel ----
            st.subheader("✏️ EDIT ROW")
            edit_id = st.number_input("ENTER ID TO EDIT", min_value=0, step=1, value=0)
            if st.button("LOAD ROW"):
                st.session_state["edit_loaded"] = int(edit_id)

            if st.session_state.get("edit_loaded"):
                rid = st.session_state["edit_loaded"]
                row_df = read_rows()
                row_df = row_df[row_df["id"] == rid]
                if row_df.empty:
                    st.warning("ID NOT FOUND.")
                else:
                    r = row_df.iloc[0]
                    with st.form("edit_form", clear_on_submit=False):
                        e1, e2, e3, e4 = st.columns(4)
                        sr = e1.number_input("SR NUMBER", value=int(r.get("sr") or 0), step=1)
                        customer = e2.text_input("CUSTOMER NAME", value=str(r.get("customer") or ""))
                        fy = e3.text_input("FINANCIAL YEAR", value=str(r.get("fy") or ""))
                        mode = e4.selectbox("MODE (SEA / AIR)", ["SEA","AIR"], index=0 if str(r.get("mode","SEA")).upper()!="AIR" else 1)

                        e5, e6, e7, e8 = st.columns(4)
                        pono = e5.text_input("PO NUMBER", value=str(r.get("pono") or ""))
                        podate = e6.date_input("PO DATE", value=pd.to_datetime(r.get("podate") or date.today(), errors="coerce").date() if r.get("podate") else date.today(), format="YYYY-MM-DD")
                        ocno = e7.text_input("OC NUMBER", value=str(r.get("ocno") or ""))
                        ocdate = e8.date_input("OC DATE", value=pd.to_datetime(r.get("ocdate") or date.today(), errors="coerce").date() if r.get("ocdate") else date.today(), format="YYYY-MM-DD")

                        e9, e10, e11 = st.columns(3)
                        description = e9.text_input("DESCRIPTION", value=str(r.get("description") or ""))
                        rate = e10.number_input("RATE (EURO)", value=float(r.get("rate") or 0.0), step=0.01)
                        ordered = e11.number_input("ORDER QUANTITY", value=float(r.get("ordered") or 0.0), step=1.0)

                        f1, f2, f3 = st.columns(3)
                        invno = f1.text_input("INVOICE NO", value=str(r.get("invno") or ""))
                        invqty = f2.number_input("INVOICE QUANTITY", value=float(r.get("invqty") or 0.0), step=1.0)
                        invdate = f3.date_input("INVOICE DATE", value=pd.to_datetime(r.get("invdate") or date.today(), errors="coerce").date() if r.get("invdate") else date.today(), format="YYYY-MM-DD")

                        g1, g2, g3, g4 = st.columns(4)
                        bldate = g1.date_input("BL DATE", value=pd.to_datetime(r.get("bldate") or date.today(), errors="coerce").date() if r.get("bldate") else date.today(), format="YYYY-MM-DD")
                        payterms = g2.selectbox("TERMS (DAYS)", options=[30,45,60], index=[30,45,60].index(int(r.get("payterms") or 30)))
                        duedate = calc_due(fmt_date(bldate), payterms)
                        g3.write(f"**DUE DATE:** {duedate or '-'}")
                        paystatus = g4.selectbox("PAYMENT STATUS", YESNO, index=0 if str(r.get("paystatus","NO")).upper()=="YES" else 1)

                        # Doc flags
                        h1, h2, h3, h4, h5, h6 = st.columns(6)
                        invoice_shared = h1.selectbox("INVOICE SHARED", YESNO, index=0 if str(r.get("invoice_shared","NO"))=="YES" else 1)
                        packing_shared = h2.selectbox("PACKING LIST SHARED", YESNO, index=0 if str(r.get("packing_shared","NO"))=="YES" else 1)
                        coa_shared     = h3.selectbox("COA SHARED", YESNO, index=0 if str(r.get("coa_shared","NO"))=="YES" else 1)
                        hd_shared      = h4.selectbox("HD SHARED", YESNO, index=0 if str(r.get("hd_shared","NO"))=="YES" else 1)
                        coo_shared     = h5.selectbox("COO SHARED", YESNO, index=0 if str(r.get("coo_shared","NO"))=="YES" else 1)
                        insurance_shared = h6.selectbox("INSURANCE SHARED", YESNO, index=0 if str(r.get("insurance_shared","NO"))=="YES" else 1)

                        remark = st.text_input("REMARK", value=str(r.get("remark") or ""))

                        if st.form_submit_button("💾 UPDATE"):
                            update_row(int(r["id"]), {
                                "sr": int(sr),
                                "customer": to_caps(customer),
                                "fy": to_caps(fy),
                                "mode": to_caps(mode),
                                "pono": to_caps(pono),
                                "podate": fmt_date(podate),
                                "ocno": to_caps(ocno),
                                "ocdate": fmt_date(ocdate),
                                "description": to_caps(description),
                                "rate": float(rate or 0),
                                "ordered": float(ordered or 0),
                                "invno": to_caps(invno),
                                "invqty": float(invqty or 0),
                                "invdate": fmt_date(invdate),
                                "bldate": fmt_date(bldate),
                                "payterms": int(payterms or 0),
                                "duedate": to_caps(duedate),
                                "paystatus": to_caps(paystatus),
                                "invoice_shared": to_caps(invoice_shared),
                                "packing_shared": to_caps(packing_shared),
                                "coa_shared": to_caps(coa_shared),
                                "hd_shared": to_caps(hd_shared),
                                "coo_shared": to_caps(coo_shared),
                                "insurance_shared": to_caps(insurance_shared),
                                "remark": to_caps(remark)
                            })
                            st.success("ROW UPDATED ✅")
                            st.rerun()

# ===================== PAGE 3: DASHBOARD (KPIs + CHARTS + PDF) =====================
elif page == "DASHBOARD":
    st.header("DASHBOARD")
    df = read_rows()

    if df.empty:
        st.info("NO DATA YET")
    else:
        invqty = pd.to_numeric(df.get("invqty", pd.Series(dtype=float)), errors="coerce").fillna(0)
        ordered = pd.to_numeric(df.get("ordered", pd.Series(dtype=float)), errors="coerce").fillna(0)
        pending_rows = (df.get("paystatus","NO").str.upper() != "YES").sum()

        c1,c2,c3 = st.columns(3)
        c1.metric("TOTAL INVOICE QUANTITY", f"{int(invqty.sum()):,}")
        c2.metric("TOTAL ORDER QUANTITY", f"{int(ordered.sum()):,}")
        c3.metric("PAYMENT PENDING (ROWS)", int(pending_rows))
        if int(pending_rows) > 0:
            st.markdown('<div class="blink" style="padding:10px;border:2px solid #ef4444;color:#ef4444;border-radius:10px;font-weight:800;text-align:center;">⚠ PAYMENT PENDING – REVIEW REQUIRED</div>', unsafe_allow_html=True)

        st.divider()

        # Prepare fields
        df_disp = df.copy()
        df_disp["customer"] = df_disp["customer"].astype(str).str.upper()
        df_disp["invqty"] = pd.to_numeric(df_disp.get("invqty", 0), errors="coerce").fillna(0)
        df_disp["rate"] = pd.to_numeric(df_disp.get("rate", 0), errors="coerce").fillna(0)
        df_disp["amount"] = df_disp["rate"] * df_disp["invqty"]

        # Quantity by Customer
        st.subheader("QUANTITY PURCHASED BY CUSTOMER")
        qty_cust = df_disp.groupby("customer", as_index=False)["invqty"].sum().sort_values("invqty", ascending=False)
        st.bar_chart(qty_cust, x="customer", y="invqty", height=300)

        # Amount by Customer
        st.subheader("AMOUNT PURCHASED BY CUSTOMER (RATE × INVOICE QTY)")
        amt_cust = df_disp.groupby("customer", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        st.bar_chart(amt_cust, x="customer", y="amount", height=300)

        # Dashboard PDF export (LANDSCAPE tables, auto-fit)
        st.subheader("EXPORT DASHBOARD")
        if REPORTLAB_OK:
            # Limit to top 20 for compact PDF tables
            qty_tbl = qty_cust.rename(columns={"customer":"CUSTOMER","invqty":"TOTAL QUANTITY"}).head(20)
            amt_tbl = amt_cust.rename(columns={"customer":"CUSTOMER","amount":"TOTAL AMOUNT (EUR)"}).head(20)
            dash_pdf = dashboard_to_pdf_bytes_landscape(
                "MIS DASHBOARD – TOP CUSTOMERS",
                [("QUANTITY BY CUSTOMER (TOP 20)", qty_tbl), ("AMOUNT BY CUSTOMER (TOP 20)", amt_tbl)]
            )
            st.download_button(
                label="⬇ DOWNLOAD DASHBOARD PDF",
                data=dash_pdf,
                file_name=f"MIS_DASHBOARD_{datetime.today().strftime('%Y-%m-%d')}.pdf",
                mime="application/pdf",
            )
        else:
            st.info("FOR PDF EXPORT: RUN `pip install reportlab`")








