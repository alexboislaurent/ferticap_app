import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


SHEET_ID = "178LJjutfRAO0cvw4aCJ2RClOuMWv1-I94X0FL8Lcs0c"

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_google_client():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )

    return gspread.authorize(creds)


@st.cache_data(ttl=60)
def load_google_data():
    """
    Charge les données principales de Google Sheets.
    Le résultat est conservé 60 secondes.
    """

    client = get_google_client()

    sheet = client.open_by_key(
        SHEET_ID
    )

    worksheet = sheet.worksheet(
        "Labo routine total"
    )

    return worksheet.get_all_values()


@st.cache_data(ttl=60)
def load_rations_data():
    """
    Charge les données de l'onglet Rations.
    Le résultat est conservé 60 secondes.
    """

    client = get_google_client()

    sheet = client.open_by_key(
        SHEET_ID
    )

    worksheet = sheet.worksheet(
        "Rations"
    )

    return worksheet.get_all_values()
