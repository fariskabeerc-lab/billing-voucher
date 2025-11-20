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

# ----------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "vouchers" not in st.session_state:
    st.session_state.vouchers = []

# ----------------------------------------------------------
# GOOGLE SHEETS CONNECTION
# ----------------------------------------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/1neEVEoAbDeW9PcjkTb3bNracxnTpsBvjYvxZ0VTYZq0/edit?gid=0"

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
    DEMO_MODE = True

# ----------------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------------
def fetch_existing_data():
    if DEMO_MODE:
        return pd.DataFrame(columns=["Name", "Number", "Bill No", "Amount", "Voucher", "Timestamp"])
    data = google_sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df

def generate_voucher(count):
    return f"VCHR-{count:05d}"

def save_to_sheet(name, mobile, bill_no, amount, voucher):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [name, mobile, bill_no, amount, voucher, timestamp]
    if DEMO_MODE:
        return
    google_sheet.append_row(row)

def bill_already_used(bill_no):
    if df.empty:
        return False
    match = df[df["Bill No"].astype(str) == str(bill_no)]
    return not match.empty

# ----------------------------------------------------------
# LOAD EXISTING DATA
# ----------------------------------------------------------
df = fetch_existing_data()

# ----------------------------------------------------------
# SHOW INSTAGRAM PAGE IF SUBMITTED
# ----------------------------------------------------------
if st.session_state.submitted:
    st.markdown(
        """
        <div style='text-align: center; margin-top: 20%;'>
            <h2>✅ To claim your voucher, please follow us on Instagram:</h2>
            <a href='https://www.instagram.com/almadinagroupuae?igsh=MTBqazJzamlzNXM3bg==' 
               target='_blank' 
               style='font-size: 24px; text-decoration: none; color: #1DA1F2;'>
               Follow us on Instagram
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # ----------------------------------------------------------
    # FORM FOR CUSTOMER DETAILS
    # ----------------------------------------------------------
    st.title("🎟️ Voucher Claim Portal")
    st.info("💡 Note: Bill Number and Amount will be fetched automatically via QR in final version. For now, enter manually.")

    st.subheader("📋 Enter Your Details")
    with st.form("details_form"):
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number")
        bill_no = st.text_input("Bill Number", value="DEMO-12345")
        amount = st.number_input("Bill Amount (AED)", min_value=1.0, value=100.0)
        submitted = st.form_submit_button("Submit")

    if submitted:
        # Validate
        if not name or not mobile or not bill_no:
            st.warning("Please fill all fields.")
            st.stop()

        if bill_already_used(bill_no):
            st.error("❌ This bill was already used to claim a voucher.")
            st.stop()

        # Calculate vouchers
        vouchers_count = math.floor(float(amount) / 50)
        if vouchers_count < 1:
            st.error("❌ Minimum AED 50 needed to earn 1 voucher.")
            st.stop()

        st.info(f"🧾 You will receive **{vouchers_count} voucher(s)** for this bill.")

        # Generate and save vouchers
        st.session_state.vouchers = []
        for i in range(vouchers_count):
            voucher_num = generate_voucher(len(df) + i + 1)
            save_to_sheet(name, mobile, bill_no, amount, voucher_num)
            st.success(f"🎟️ Voucher Generated: {voucher_num}")
            st.session_state.vouchers.append(voucher_num)

        # Balloons animation
        st.balloons()

        # Set session state to show Instagram page next
        st.session_state.submitted = True
