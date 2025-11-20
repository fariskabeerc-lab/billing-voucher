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
# READ QR PARAMETERS
# Example QR: ?bill_no=123&amount=85
# ----------------------------------------------------------
query_params = st.query_params

bill_no = query_params.get("bill_no", "")
amount = query_params.get("amount", "")

# For DEMO mode → auto-fill sample values
if not bill_no:
    bill_no = "DEMO-12345"

if not amount:
    amount = "100"

st.info(f"🧾 **Bill No:** {bill_no} | 💰 **Amount:** {amount} AED")

# ----------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------
def fetch_existing_data():
    """Read entire sheet into a DataFrame."""
    if DEMO_MODE:
        return pd.DataFrame(columns=["Name", "Number", "Bill No", "Amount", "Voucher", "Timestamp"])

    data = google_sheet.get_all_records()
    return pd.DataFrame(data)


def generate_voucher(count):
    """Generates formatted voucher number: VCHR-00001"""
    return f"VCHR-{count:05d}"


def save_to_sheet(name, mobile, bill_no, amount, voucher):
    """Save new row to Google Sheets."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [name, mobile, "", "", "", bill_no, amount, voucher, timestamp]

    if DEMO_MODE:
        st.success(f"[DEMO] Row saved: {row}")
        return

    google_sheet.append_row(row)


# ----------------------------------------------------------
# LOAD EXISTING DATA
# ----------------------------------------------------------
df = fetch_existing_data()

# ----------------------------------------------------------
# CHECK IF MOBILE ALREADY HAS A VOUCHER
# ----------------------------------------------------------
def get_existing_voucher(mobile):
    if df.empty:
        return None

    match = df[df["Number"].astype(str) == str(mobile)]
    if match.empty:
        return None

    return match.iloc[0]["Voucher"]

# ----------------------------------------------------------
# CHECK IF BILL ALREADY USED
# ----------------------------------------------------------
def bill_already_used(bill_no):
    if df.empty:
        return False

    match = df[df["Bill No"].astype(str) == str(bill_no)]
    return not match.empty


# ----------------------------------------------------------
# FORM FOR CUSTOMER DETAILS
# ----------------------------------------------------------
st.subheader("📋 Enter Your Details")

with st.form("details_form"):
    name = st.text_input("Full Name")
    mobile = st.text_input("Mobile Number")
    submitted = st.form_submit_button("Submit")


# ----------------------------------------------------------
# PROCESS FORM
# ----------------------------------------------------------
if submitted:

    if not name or not mobile:
        st.warning("Please fill all fields.")
        st.stop()

    # Check if mobile already received voucher
    existing_voucher = get_existing_voucher(mobile)
    if existing_voucher:
        st.success(f"🎉 You already have a voucher: **{existing_voucher}**")
        st.info("You cannot receive multiple vouchers with the same number.")
        st.stop()

    # Check if bill already claimed
    if bill_already_used(bill_no):
        st.error("❌ This bill was already used to claim a voucher.")
        st.stop()

    # Calculate vouchers based on amount
    vouchers_count = math.floor(float(amount) / 50)

    if vouchers_count < 1:
        st.error("❌ Minimum AED 50 needed to earn 1 voucher.")
        st.stop()

    # Create new voucher
    voucher_num = generate_voucher(len(df) + 1)

    # Save to Google Sheet
    save_to_sheet(name, mobile, bill_no, amount, voucher_num)

    st.success(f"🎉 **Voucher Generated: {voucher_num}**")
    st.info(f"🧾 You earned **{vouchers_count} voucher(s)** from this bill.")

    st.balloons()
