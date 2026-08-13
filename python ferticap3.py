import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import calendar
import numpy as np
import random
import os
from analysis.ranking import calc_ranking_with_success
from plots.heatmap import create_heatmap
from plots.scores import create_score_global
from plots.score_bouc import create_score_bouc
from plots.ranking import show_ranking
from streamlit_autorefresh import st_autorefresh
from plots.calendrier import afficher_calendrier
from plots.variables_biologiques import afficher_variables_biologiques
from plots.variables_physio import afficher_variables_physio
from plots.bouc_tv import afficher_bouc_tv

# =========================
# CONFIG PAGE
# =========================

st.set_page_config(page_title="Ferticap Dashboard", layout="wide")

# =========================
# MODE ECRAN TV
# =========================

DUREE_ECRAN_TV = 15  # secondes

MODES_TV = [
    "Heatmap",
    "Bouc TV",
    "Score global",
    "Bouc TV",
    "Score par bouc",
    "Bouc TV",
    "Variables biologiques",
    "Bouc TV",
    "Variables physiologiques",
    "Bouc TV",
    "🏆 Ranking boucs",
    "Bouc TV",
    "📅 Calendrier",
    "Bouc TV"
]

# =========================
# INDICATEUR JOURS LONGS / COURTS
# =========================

date_actuelle = pd.Timestamp.today()
mois_actuel = date_actuelle.month

mois_jours_longs = [12, 1, 4, 5, 8, 9]

if mois_actuel in mois_jours_longs:
    indicateur = "🟡"
    texte_jour = "Jours longs actuellement"
else:
    indicateur = "🔵"
    texte_jour = "Jours courts actuellement"


# =========================
# TITRE
# =========================

col1, col2 = st.columns([3, 2])

with col1:
    st.title("📊 Dashboard Ferticap")

with col2:
    st.markdown(
        f"### {indicateur} {texte_jour}"
    )
# =========================
# CONNEXION GOOGLE SHEETS
# =========================

from data.google_sheet import load_google_sheet

worksheet = load_google_sheet()


# =========================
# DATA
# =========================
from data.cleaning import clean_data


all_values = worksheet.get_all_values()

df = clean_data(all_values)
# =========================
# VARIABLE SUIVI DES SAUTS
# =========================

df["Suivi des sauts"] = (
    df["Comportement"]
    .isin([2, 3, 4])
    .astype(int)
)

df["Code animal"] = df["Code animal"].astype(str).str.strip()

df = df[df["Code animal"].notna()]
df = df[df["Code animal"] != ""]
df = df.dropna(subset=["Date"])

# =========================
# VARIABLES BIOLOGIQUES
# =========================

variables_map = {
    "Volume semence (ml)": "Volume semence (ml)",
    "Concentration spz (B/ml)": "Concentration spz (B/ml)",
    "Nb spz éjaculat (B)": "Nb spz éjaculat (B)",
    "% Mobiles": "% Mobiles",
    "Motiles": "Motiles",
    "Suivi des sauts": "Suivi des sauts"
}

for col in variables_map.values():
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "."),
            errors="coerce"
        )

# =========================
# SIDEBAR
# =========================

st.sidebar.header("📌 Options")

mode_tv = st.sidebar.checkbox(
    "🖥️ Mode écran TV",
    value=False
)

if mode_tv:

    compteur_tv = st_autorefresh(
        interval=DUREE_ECRAN_TV * 1000,
        key="rotation_tv"
    )

    # UNE SEULE page à la fois
    mode = MODES_TV[
        compteur_tv % len(MODES_TV)
    ]

else:

    mode = st.sidebar.radio(
    "Graph à afficher",
    [
        "Heatmap",
        "Score global",
        "Score par bouc",
        "Variables biologiques",
        "Variables physiologiques",
        "🏆 Ranking boucs",
        "📅 Calendrier"
    ]
)

# =========================
# INFO SCORE
# =========================

with st.sidebar.expander("ℹ️ Méthode de calcul du score"):
    st.markdown("""
Le score est calculé à partir d’un éjaculat selon la formule suivante :

**Score = (Concentration (B/ml) × Volume éjaculat (ml)) × (% Mobilité) × ((Motilité × 2) / 100)**

### ⚠️ Règle spécifique
- Si la motilité ≤ 2,5 → le score est plafonné à **0,99**

### 📌 Prend en compte :
- Concentration*Volume = Total spz dans l'éjaculat en (M/ml)
- La mobilité pondère la proportion de spermatozoïdes mobiles
- La motilité ajuste la qualité du mouvement

- Un score inférieur à 1 est un mauvais éjaculat, non exploitable
""")

# =========================
# FILTRE DATES
# =========================

df = df.dropna(subset=["Date"])

# =========================
# PREPARATION  SUIVIS
# =========================

suivi_cols = ["Suivi 1", "Suivi 2", "Suivi 3", "Suivi 4"]
existing_cols = [c for c in suivi_cols if c in df.columns]

df_suivi = df.melt(
    id_vars=["Date"],
    value_vars=existing_cols,
    value_name="Suivi"
)

daily = (
    df_suivi.dropna(subset=["Suivi"])
    .groupby("Date")["Suivi"]
    .apply(list)
    .reset_index()
)

df_suivi = df_suivi.dropna(subset=["Suivi"])
df_suivi = df_suivi[df_suivi["Suivi"].astype(str).str.strip() != ""]

# =========================
# FILTRE DATES
# =========================

df = df.dropna(subset=["Date"])

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

# 1 an glissant par défaut
date_debut_1_an = (
    pd.Timestamp(max_date) - pd.DateOffset(years=1)
).date()

# Ne pas aller avant la première donnée disponible
date_debut_1_an = max(
    date_debut_1_an,
    min_date
)

date_range = st.sidebar.slider(
    "Période d'analyse",
    min_value=min_date,
    max_value=max_date,
    value=(date_debut_1_an, max_date)
)

start_date, end_date = date_range

df_filtered = df[
    (df["Date"] >= pd.to_datetime(start_date)) &
    (df["Date"] <= pd.to_datetime(end_date))
]

start_date, end_date = date_range

df_filtered = df[
    (df["Date"] >= pd.to_datetime(start_date)) &
    (df["Date"] <= pd.to_datetime(end_date))
]

# =========================
# RANKING BOUCS (10 DERNIÈRES COLLECTES) ✔ FIXÉ
# =========================

last_10_dates = sorted(df_filtered["Date"].dropna().unique())[-10:]

df_last10 = df_filtered[df_filtered["Date"].isin(last_10_dates)]

ranking_df = (
    df_last10.groupby("Code animal", as_index=False)["Score"]
    .mean()
    .sort_values("Score", ascending=False)
)

ranking_df = ranking_df.rename(columns={
    "Code animal": "Boucs",
    "Score": "Score moyen (10 dernières)"
})

# =========================
# BOUCS AUTO DERNIÈRE COLLECTE
# =========================

boucs = sorted(df["Code animal"].unique())

last_date = df_filtered["Date"].max()

boucs_derniere_collecte = (
    df_filtered[df_filtered["Date"] == last_date]["Code animal"]
    .dropna()
    .unique()
    .tolist()
)

# Sécurité si aucune collecte dans la période
if len(boucs_derniere_collecte) == 0:
    boucs_derniere_collecte = boucs.copy()

# =========================
# BOUC POUR L'AFFICHAGE TV
# =========================

bouc_tv = None

if mode_tv and boucs_derniere_collecte:

    # Nombre de passages sur "Bouc TV"
    # avant le passage actuel
    nb_passages_bouc = sum(
        1
        for i in range(compteur_tv + 1)
        if MODES_TV[i % len(MODES_TV)] == "Bouc TV"
    ) - 1

    bouc_tv = boucs_derniere_collecte[
        nb_passages_bouc % len(boucs_derniere_collecte)
    ]

# Boucs actuels en premier
boucs = (
    sorted(boucs_derniere_collecte)
    + sorted([b for b in boucs if b not in boucs_derniere_collecte])
)

st.sidebar.markdown("### 🐐 Sélection des boucs")

# Case pour sélectionner automatiquement les boucs actuels
if st.sidebar.button("🟢 Sélectionner les boucs actuels"):
    for b in boucs:
        st.session_state[f"bouc_{b}"] = b in boucs_derniere_collecte

# Boutons rapides
if st.sidebar.button("☑ Tout sélectionner"):
    for b in boucs:
        st.session_state[f"bouc_{b}"] = True

if st.sidebar.button("☐ Tout désélectionner"):
    for b in boucs:
        st.session_state[f"bouc_{b}"] = False


selected_boucs = []

for b in boucs:

    # Valeur par défaut au premier affichage
    if f"bouc_{b}" not in st.session_state:
        st.session_state[f"bouc_{b}"] = (
            b in boucs_derniere_collecte
        )

    label = (
        f"🟢 {b}"
        if b in boucs_derniere_collecte
        else f"⚪ {b}"
    )

    if st.sidebar.checkbox(
        label,
        key=f"bouc_{b}"
    ):
        selected_boucs.append(b)


# =========================
# PARAMÈTRES
# =========================

periode = st.sidebar.selectbox(
    "Regroupement temporel",
    ["Jour", "Semaine", "2 semaines", "Mois"],
    index=2
)

lissage = st.sidebar.select_slider(
    "Lissage (0 = aucun)",
    options=[0, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    value=0
)

# =========================
# PREP DATA
# =========================

heatmap = df_filtered.pivot_table(
    index="Code animal",
    columns="Date",
    values="Succes",
    aggfunc="max"
).sort_index(axis=1)

# Format JJ/MM/AA
heatmap.columns = heatmap.columns.strftime("%d/%m/%y")

score_global = (
    df_filtered.groupby("Date")["Score"]
    .mean()
    .dropna()
    .sort_index()
)

score_par_bouc = df_filtered.pivot_table(
    index="Date",
    columns="Code animal",
    values="Score",
    aggfunc="mean"
).sort_index()

# 10 dernières collectes
last_10_dates = sorted(
    df_filtered["Date"].dropna().unique()
)[-10:]

df_last10 = df_filtered[
    df_filtered["Date"].isin(last_10_dates)
]

# Année en cours
current_year = pd.Timestamp.today().year

df_year = df_filtered[
    df_filtered["Date"].dt.year == current_year
]

ranking_last10 = calc_ranking_with_success(df_last10)
ranking_year = calc_ranking_with_success(df_year)
ranking_alltime = calc_ranking_with_success(df)

# =========================
# RESAMPLE
# =========================

def resample_series(series):
    if periode == "Jour":
        return series
    if periode == "Semaine":
        return series.resample("W").mean()
    if periode == "2 semaines":
        return series.resample("2W").mean()
    if periode == "Mois":
        return series.resample("ME").mean()
    return series
    
def resample_series_physio(series):
    if periode_physio == "Jour":
        return series
    if periode_physio == "Semaine":
        return series.resample("W").mean()
    if periode_physio == "2 semaines":
        return series.resample("2W").mean()
    if periode_physio == "Mois":
        return series.resample("ME").mean()
    return series

def get_color(suivis):
    if len(suivis) > 1:
        return "purple"
    if "FCO" in suivis:
        return "red"
    if "LNCR" in suivis:
        return "blue"
    return "gray"


# =========================
# AFFICHAGE
# =========================

if mode == "Heatmap":

    st.subheader("Heatmap succès")

    fig = create_heatmap(heatmap)

    st.pyplot(fig)


elif mode == "Bouc TV":

    afficher_bouc_tv(
        df_filtered,
        bouc_tv
    )


elif mode == "Score global":

    st.subheader("Score moyen global")

    score = resample_series(score_global)

    fig = create_score_global(
        score,
        lissage
    )

    st.pyplot(fig)


elif mode == "Score par bouc":

    st.subheader("Score par bouc")

    data = resample_series(score_par_bouc)

    fig = create_score_bouc(
        data,
        selected_boucs,
        lissage
    )

    st.pyplot(fig)

elif mode == "Variables biologiques":

    afficher_variables_biologiques(
        df_filtered=df_filtered,
        selected_boucs=selected_boucs,
        periode=periode,
        lissage=lissage,
    )


elif mode == "Variables physiologiques":

    afficher_variables_physio(
        df_filtered=df_filtered,
        selected_boucs=selected_boucs,
    )

elif mode == "🏆 Ranking boucs":

    show_ranking(
        ranking_last10,
        ranking_year,
        ranking_alltime,
        current_year
    )


elif mode == "📅 Calendrier":

    afficher_calendrier(df)
