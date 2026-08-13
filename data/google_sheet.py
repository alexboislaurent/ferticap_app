import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


def load_google_sheet():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_key(
        "178LJjutfRAO0cvw4aCJ2RClOuMWv1-I94X0FL8Lcs0c"
    )

    worksheet = sheet.worksheet(
        "Labo routine total"
    )

    return worksheet

def load_rations_sheet():

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = client.open_by_key(
        "178LJjutfRAO0cvw4aCJ2RClOuMWv1-I94X0FL8Lcs0c"
    )

    worksheet = sheet.worksheet(
        "Rations"
    )

    return worksheet
