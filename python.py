import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import math

# Hide Streamlit menu and footer
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# ------------------ PAGE SETUP ------------------
st.set_page_config(page_title="Voucher Claim", layout="centered")
st.title("🎟️ Voucher Claim Portal")
st.info("💡 Note: Bill Number and Amount will be fetched via QR code in final version. For now, enter manually.")

# ------------------ GOOGLE SHEETS CONNECTION ------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1neEVEoAbDeW9PcjkTb3bNracxnTpsBvjYvxZ0VTYZq0/edit?gid=0"
SCOPE = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

google_sheet = None
DEMO_MODE = False

try:
    creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
    client = gspread.authorize(creds)
    google_sheet = client.open_by_url(SHEET_URL).sheet1
except Exception:
    st.warning("⚠️ Unable to connect to Google Sheets. Running in demo mode.")
    DEMO_MODE = True

# ------------------ HELPER FUNCTIONS ------------------
def fetch_existing_data():
    if DEMO_MODE:
        return pd.DataFrame(columns=["Name","Number","Nationality","Amount","Bill No","Address","Email","Voucher","Timestamp"])
    data = google_sheet.get_all_records()
    df = pd.DataFrame(data)
    # Normalize column names
    df.columns = [str(col).strip() for col in df.columns]
    return df

def generate_voucher(count):
    return f"VCHR-{count:05d}"

def save_to_sheet(name, mobile, nationality, amount, bill_no, address, email, voucher):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [name, mobile, nationality, amount, bill_no, address, email, voucher, timestamp]
    if DEMO_MODE:
        st.success(f"[DEMO] Row saved: {row}")
        return
    google_sheet.append_row(row)

def already_claimed(df, bill_no, mobile):
    """Check if the combination of bill_no and mobile already exists."""
    if df.empty:
        return False
    match = df[
        (df["Bill No"].astype(str) == str(bill_no)) &
        (df["Number"].astype(str) == str(mobile))
    ]
    return not match.empty

# ------------------ FORM ------------------
st.subheader("📋 Enter Your Details")
with st.form("details_form"):
    name = st.text_input("Full Name")
    mobile = st.text_input("Mobile Number")
    nationality = st.text_input("Nationality")
    bill_no = st.text_input("Bill Number")
    amount = st.number_input("Bill Amount (AED)", min_value=1.0, value=50.0)
    address = st.text_input("Address")
    email = st.text_input("Email")
    submitted = st.form_submit_button("Submit")

# ------------------ PROCESS FORM ------------------
if submitted:
    if not all([name, mobile, bill_no, amount]):
        st.warning("Please fill all required fields.")
        st.stop()

    # Reload latest sheet data
    df = fetch_existing_data()

    # Check restriction
    if already_claimed(df, bill_no, mobile):
        st.error("❌ This mobile number has already claimed a voucher for this bill.")
        st.stop()

    # Calculate vouchers
    vouchers_count = math.floor(float(amount) / 50)
    if vouchers_count < 1:
        st.error("❌ Minimum AED 50 needed to earn 1 voucher.")
        st.stop()

    st.info(f"🧾 You will receive **{vouchers_count} voucher(s)** for this bill.")

    # Generate and save vouchers
    for i in range(vouchers_count):
        voucher_num = generate_voucher(len(df) + i + 1)
        save_to_sheet(name, mobile, nationality, amount, bill_no, address, email, voucher_num)
        st.success(f"🎟️ Voucher Generated: {voucher_num}")

    # Balloon animation
    st.balloons()

    # Clear screen and show Instagram message
    st.empty()
    st.markdown(
        "<h1 style='text-align:center; color:green;'>✅ To claim your voucher, please follow us on Instagram</h1>"
        "<h2 style='text-align:center;'><a href='https://www.instagram.com/almadinagroupuae/' target='_blank'>Follow us on Instagram</a></h2>",
        unsafe_allow_html=True,
    )
