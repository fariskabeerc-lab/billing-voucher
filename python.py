import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import math
import json

# ----------------------------
# Google Sheet Setup
# ----------------------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

# Load credentials from Streamlit secrets
creds_info = json.loads(st.secrets["gcp_service_account"])
CREDS = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
GC = gspread.authorize(CREDS)

# Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1neEVEoAbDeW9PcjkTb3bNracxnTpsBvjYvxZ0VTYZq0/edit?gid=0"
SHEET = GC.open_by_url(SHEET_URL).sheet1

# ----------------------------
# Fetch query params (QR code) or demo mode
# ----------------------------
query_params = st.experimental_get_query_params()
bill_no = query_params.get("bill_no", ["DEMO123"])[0]  # demo default
amount = query_params.get("amount", ["150"])[0]        # demo default

# Convert amount to float
try:
    amount = float(amount)
except:
    amount = 150  # fallback demo amount

st.title("🎁 Voucher Claim Form (Demo Mode)")
st.write(f"Bill No: **{bill_no}** | Amount: **{amount} AED**")

# ----------------------------
# Customer Form
# ----------------------------
with st.form("customer_form"):
    name = st.text_input("Full Name")
    number = st.text_input("Mobile Number (with country code, e.g., 97150xxxxxxx)")
    nationality = st.text_input("Nationality (optional)")
    email = st.text_input("Email (optional)")
    address = st.text_input("Address (optional)")
    instagram = st.checkbox("Follow our Instagram to claim voucher (informational)")
    submitted = st.form_submit_button("Submit")

if submitted:
    if not name or not number:
        st.error("Name and Mobile Number are required!")
        st.stop()

    # ----------------------------
    # Fetch all records from Google Sheet
    # ----------------------------
    all_records = SHEET.get_all_records()

    # Check if number exists for this bill
    existing_voucher = None
    for record in all_records:
        if str(record['Number']) == number and str(record['Bill No']) == bill_no:
            existing_voucher = record
            break

    # Calculate number of vouchers
    vouchers_to_generate = math.floor(amount / 50)
    if vouchers_to_generate < 1:
        vouchers_to_generate = 1  # minimum 1 voucher

    # ----------------------------
    # Voucher Logic
    # ----------------------------
    if existing_voucher:
        st.info(f"This mobile number has already claimed voucher(s) for Bill No {bill_no}.")
        st.success(f"Voucher(s) already issued.")
    else:
        # Determine last voucher number
        last_voucher_row = len(all_records)
        voucher_numbers = []
        for i in range(vouchers_to_generate):
            voucher_no = f"VCHR-{last_voucher_row + i + 1:05d}"
            voucher_numbers.append(voucher_no)

        # Append new row to Google Sheet
        new_row = [name, number, nationality, email, address, bill_no, amount]
        SHEET.append_row(new_row)

        st.success(f"Voucher(s) generated: {', '.join(voucher_numbers)}")

        # ----------------------------
        # WhatsApp sending placeholder (just a mark)
        # ----------------------------
        # Here you could integrate WhatsApp Cloud API to send the voucher
        # Example:
        # send_whatsapp(number, voucher_numbers)
        st.info("Voucher has been sent to your WhatsApp (placeholder mark only).")
