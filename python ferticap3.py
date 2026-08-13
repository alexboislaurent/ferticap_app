import pandas as pd
import streamlit as st

from streamlit_autorefresh import st_autorefresh

from analysis.ranking import calc_ranking_with_success

from data.google_sheet import (
    load_google_data,
    load_rations_data,
)

from data.cleaning import clean_data
from data.boucs import (
    preparer_boucs,
    get_bouc_tv,
    afficher_selection_boucs,
)

from plots.heatmap import create_heatmap
from plots.scores import create_score_global
from plots.score_bouc import create_score_bouc
from plots.ranking import show_ranking
from plots.calendrier import afficher_calendrier
from plots.variables_biologiques import afficher_variables_biologiques
from plots.variables_physio import afficher_variables_physio
from plots.bouc_tv import afficher_bouc_tv
from plots.rations import afficher_rations
from plots.boucs_surveillance import afficher_boucs_surveillance

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
    "Rations",
    "🚨 Boucs à surveiller",
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
# CONNEXION GOOGLE SHEETS
# =========================

all_values = load_google_data()
rations_values = load_rations_data()

# =========================
# DATA
# =========================

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
        "📅 Calendrier",
        "Rations",
        "Bouc TV"
    ]
)

# =========================
# TITRE
# =========================

if mode != "Bouc TV":

    col1, col2 = st.columns([3, 2])

    with col1:
        st.title("📊 Dashboard Ferticap")

    with col2:
        st.markdown(
            f"### {indicateur} {texte_jour}"
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

# =========================
# BOUCS
# =========================

boucs, boucs_derniere_collecte = preparer_boucs(
    df,
    df_filtered,
)

bouc_tv = get_bouc_tv(
    mode_tv,
    compteur_tv if mode_tv else 0,
    MODES_TV,
    boucs_derniere_collecte,
)

selected_boucs = afficher_selection_boucs(
    boucs,
    boucs_derniere_collecte,
)

# =========================
# BOUC MANUEL
# =========================

bouc_manuel = None

if not mode_tv:

    if len(selected_boucs) == 1:

        bouc_manuel = selected_boucs[0]

    elif len(selected_boucs) > 1:

        bouc_manuel = st.sidebar.selectbox(
            "🐐 Bouc à afficher",
            selected_boucs,
            key="bouc_manuel"
        )

    else:

        st.sidebar.info(
            "Sélectionnez un bouc dans la liste."
        )
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

# =========================
# RANKING
# =========================

last_10_dates = sorted(
    df_filtered["Date"].dropna().unique()
)[-10:]

df_last10 = df_filtered[
    df_filtered["Date"].isin(last_10_dates)
]

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
# =========================
# AFFICHAGE
# =========================

if mode == "Heatmap":

    st.subheader("Heatmap succès")

    fig = create_heatmap(heatmap)

    st.pyplot(fig)


elif mode == "Bouc TV":

    bouc_a_afficher = (
        bouc_tv
        if mode_tv
        else bouc_manuel
    )

    afficher_bouc_tv(
        df_filtered,
        bouc_a_afficher,
        df_historique=df
    )


elif mode == "Score global":

    st.subheader("Score moyen global")

    score = resample_series(score_global)

    fig = create_score_global(
        score,
        lissage
    )

    st.pyplot(fig)

elif mode == "🚨 Boucs à surveiller":

    afficher_boucs_surveillance(
        df,
        boucs_derniere_collecte
    )


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

elif mode == "Rations":

    afficher_rations(
        rations_values
    )


elif mode == "📅 Calendrier":

    afficher_calendrier(df)
