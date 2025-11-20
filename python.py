import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import math

# ----------------------------------------------------------
# PAGE SETUP
# ----------------------------------------------------------
st.set_page_config(page_title="Voucher Claim", layout="centered")
st.title("🎟️ Voucher Claim Portal")


# ----------------------------------------------------------
# GOOGLE SHEETS CONNECTION
# ----------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1neEVEoAbDeW9PcjkTb3bNracxnTpsBvjYvxZ0VTYZq0/edit?gid=0#gid=0"

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

google_sheet = None
DEMO_MODE = False

try:
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"], scopes=SCOPE
    )
    client = gspread.authorize(creds)
    google_sheet = client.open_by_url(SHEET_URL).sheet1

except Exception:
    st.warning("⚠️ Unable to connect to Google Sheets. Running in demo mode.")
    DEMO_MODE = True


# ----------------------------------------------------------
# HELPER: Fetch Sheet Data
# ----------------------------------------------------------
def fetch_existing_data():
    """Read entire sheet into a DataFrame."""
    if DEMO_MODE:
        return pd.DataFrame(columns=["Name", "Number", "Bill No", "Amount", "Voucher", "Timestamp"])

    data = google_sheet.get_all_records()
    return pd.DataFrame(data)


df = fetch_existing_data()


# ----------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------
def generate_voucher(count):
    """Generate voucher like VCHR-00001"""
    return f"VCHR-{count:05d}"


def save_to_sheet(name, mobile, bill_no, amount, voucher):
    """Save new row to Google Sheets."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [name, mobile, "", "", "", bill_no, amount, voucher, timestamp]

    if DEMO_MODE:
        st.success(f"[DEMO] Row saved locally: {row}")
        return

    google_sheet.append_row(row)


def get_existing_voucher(mobile):
    if df.empty:
        return None
    match = df[df["Number"].astype(str) == str(mobile)]
    if match.empty:
        return None
    return match.iloc[0]["Voucher"]


def bill_already_used(bill_no):
    if df.empty:
        return False
    match = df[df["Bill No"].astype(str) == str(bill_no)]
    return not match.empty


# ----------------------------------------------------------
# NEW: BILL ENTRY SECTION (Manual Demo Entry)
# ----------------------------------------------------------
st.subheader("🧾 Enter Bill Details (Demo/Manual Mode)")

with st.form("bill_form"):
    bill_no = st.text_input("Bill Number", placeholder="Enter Bill Number")
    bill_amount = st.number_input("Bill Amount (AED)", min_value=1, step=1)
    bill_submit = st.form_submit_button("Confirm Bill")

if not bill_submit:
    st.stop()

if not bill_no or bill_amount <= 0:
    st.error("Please enter a valid Bill No and Amount.")
    st.stop()

st.success(f"Bill Loaded → **{bill_no} | {bill_amount} AED**")


# ----------------------------------------------------------
# CUSTOMER DETAILS FORM
# ----------------------------------------------------------
st.subheader("👤 Enter Your Details")

with st.form("customer_form"):
    name = st.text_input("Full Name")
    mobile = st.text_input("Mobile Number")
    submitted = st.form_submit_button("Claim Voucher")

# ----------------------------------------------------------
# PROCESS CUSTOMER CLAIM
# ----------------------------------------------------------
if submitted:

    if not name or not mobile:
        st.warning("Please fill all fields.")
        st.stop()

    existing_voucher = get_existing_voucher(mobile)
    if existing_voucher:
        st.success(f"🎉 You already have a voucher: **{existing_voucher}**")
        st.info("One voucher per mobile number.")
        st.stop()

    if bill_already_used(bill_no):
        st.error("❌ This bill was already used to claim a voucher.")
        st.stop()

    voucher_count = math.floor(float(bill_amount) / 50)
    if voucher_count < 1:
        st.error("❌ Minimum AED 50 required for 1 voucher.")
        st.stop()

    voucher_no = generate_voucher(len(df) + 1)

    save_to_sheet(name, mobile, bill_no, bill_amount, voucher_no)

    st.success(f"🎉 Voucher Generated: **{voucher_no}**")
    st.info(f"🧾 You earned **{voucher_count} voucher(s)** from this bill.")

    st.balloons()   # <-- 🎈🎈🎈 BALLOONS HERE 🎈🎈🎈
