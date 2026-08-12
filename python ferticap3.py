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
    "🏆 Ranking boucs",
    "Bouc TV",
    "📅 Calendrier",
    "Bouc TV"
]

st.title("📊 Dashboard Ferticap")

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
# PREPARATION CALENDRIER SUIVIS
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

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

date_range = st.sidebar.slider(
    "Période d'analyse",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

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
    ["Jour", "Semaine", "2 semaines", "Mois"]
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

def get_color(suivis):
    if len(suivis) > 1:
        return "purple"
    if "FCO" in suivis:
        return "red"
    if "LNCR" in suivis:
        return "blue"
    return "gray"

# =========================
# FICHE BOUC MODE TV
# =========================

def afficher_bouc_tv(df, bouc):

    data_bouc = df[
        df["Code animal"] == bouc
    ].copy()

    data_2026 = data_bouc[
        data_bouc["Date"].dt.year == 2026
    ]

    # =========================
    # PERFORMANCES
    # =========================

    nb_sauts = (
        data_2026["Comportement"]
        .isin([2, 3, 4])
        .sum()
    )

    volume_moyen = pd.to_numeric(
        data_2026["Volume semence (ml)"],
        errors="coerce"
    ).mean()

    concentration_moyenne = pd.to_numeric(
        data_2026["Concentration spz (B/ml)"],
        errors="coerce"
    ).mean()

    nb_collectes = len(data_2026)

    # =========================
    # PHOTO
    # =========================

    photo = f"images/bouc_{bouc}.jpg"

    # =========================
    # AFFICHAGE
    # =========================

    st.markdown(
        f"""
        <div style="
            text-align:center;
            margin-bottom:20px;
        ">
            <h1>🐐 Bouc {bouc}</h1>
            <h2>Performances 2026</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_photo, col_stats = st.columns(
        [1.3, 1]
    )

    # =========================
    # PHOTO
    # =========================

    with col_photo:

        if os.path.exists(photo):

            st.image(
                photo,
                width=550
            )

        else:

            st.warning(
                f"📷 Photo non disponible pour le bouc {bouc}"
            )

    # =========================
    # STATISTIQUES
    # =========================

    with col_stats:

        volume_txt = (
            f"{volume_moyen:.1f} ml"
            if pd.notna(volume_moyen)
            else "—"
        )

        concentration_txt = (
            f"{concentration_moyenne:.1f} B/ml"
            if pd.notna(concentration_moyenne)
            else "—"
        )

        st.markdown(
            f"""
            <div style="
                padding:30px;
                border-radius:20px;
                border:2px solid #ddd;
                text-align:center;
                margin-top:20px;
            ">

            <h2>📊 Performances</h2>

            <h3>🦘 Nombre de sauts</h3>
            <h1>{nb_sauts}</h1>

            <h3>💧 Volume moyen</h3>
            <h1>{volume_txt}</h1>

            <h3>🔬 Concentration moyenne</h3>
            <h1>{concentration_txt}</h1>

            <h3>📅 Nombre de collectes</h3>
            <h1>{nb_collectes}</h1>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================
# HEATMAP
# =========================

if mode == "Heatmap":

    st.subheader("Heatmap succès")

    fig = create_heatmap(heatmap)

    st.pyplot(fig)

# =========================
# BOUC TV
# =========================

elif mode == "Bouc TV":

    afficher_bouc_tv(
        df,
        bouc_tv
    )

# =========================
# SCORE GLOBAL
# =========================

elif mode == "Score global":

    st.subheader("Score moyen global")

    score = resample_series(score_global)

    fig = create_score_global(
        score,
        lissage
    )

    st.pyplot(fig)
# =========================
# SCORE PAR BOUC
# =========================
elif mode == "Score par bouc":

    st.subheader("Score par bouc")

    data = resample_series(score_par_bouc)

    fig = create_score_bouc(
        data,
        selected_boucs,
        lissage
    )

    st.pyplot(fig)

# =========================
# VARIABLES BIOLOGIQUES
# =========================

elif mode == "Variables biologiques":

    st.subheader("📊 Variables biologiques")


    selected_vars = st.sidebar.multiselect(
        "Variables biologiques",
        list(variables_map.keys()),
        default=[
            "Volume semence (ml)",
            "Concentration spz (B/ml)"
        ]
    )


    filtrer_boucs = st.sidebar.checkbox(
        "Filtrer par boucs sélectionnés",
        value=False
    )


    afficher_individuels = st.sidebar.checkbox(
        "Afficher une courbe par bouc",
        value=False
    )


    # =========================
    # CHOIX DES DONNEES
    # =========================

    if filtrer_boucs:

        if len(selected_boucs) == 0:

            st.warning(
                "Aucun bouc sélectionné."
            )

            st.stop()


        data_bio = df_filtered[
            df_filtered["Code animal"].isin(selected_boucs)
        ].copy()


    else:

        # identique à l'ancien fonctionnement
        data_bio = df_filtered.copy()



    if data_bio.empty:

        st.warning(
            "Aucune donnée disponible."
        )

        st.stop()



    fig, ax = plt.subplots(
        figsize=(14, 6)
    )



    # =========================
    # FONCTION LISSAGE
    # =========================

    def appliquer_lissage(serie):

        if lissage <= 1:
            return serie

        return (
            serie
            .rolling(
                window=lissage,
                min_periods=1
            )
            .mean()
        )



       # =========================
    # TRACE VARIABLES
    # =========================

    for var in selected_vars:

        col = variables_map[var]


        if col not in data_bio.columns:

            st.warning(
                f"Variable absente : {col}"
            )

            continue


        # Nettoyage valeurs
        data_bio[col] = (
            data_bio[col]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
        )


        data_bio[col] = pd.to_numeric(
            data_bio[col],
            errors="coerce"
        )


        # =========================
        # COURBES INDIVIDUELLES
        # =========================

        if afficher_individuels:

            for b in selected_boucs:

                data_bouc = data_bio[
                    data_bio["Code animal"] == b
                ]


                # Suivi des sauts = somme des sauts
                if col == "Suivi des sauts":

                    serie = (
                        data_bouc
                        .groupby("Date")[col]
                        .sum()
                        .sort_index()
                        .fillna(0)
                    )


                # Variables biologiques = moyenne
                else:

                    serie = (
                        data_bouc
                        .groupby("Date")[col]
                        .mean()
                        .sort_index()
                        .fillna(0)
                    )


                if len(serie) > 0:

                    serie = resample_series(serie)


                    # Lissage uniquement variables continues
                    if col != "Suivi des sauts" and lissage > 1:

                        serie = (
                            serie
                            .rolling(
                                window=lissage,
                                min_periods=1
                            )
                            .mean()
                        )


                    ax.plot(
                        serie.index,
                        serie.values,
                        marker="o",
                        label=f"{var} - {b}"
                    )


        # =========================
        # MOYENNE GENERALE
        # =========================

        else:

            if col == "Suivi des sauts":

                serie = (
                    data_bio
                    .groupby("Date")[col]
                    .sum()
                    .sort_index()
                    .fillna(0)
                )


            else:

                serie = (
                    data_bio
                    .groupby("Date")[col]
                    .mean()
                    .sort_index()
                    .fillna(0)
                )


            if len(serie) > 0:

                serie = resample_series(serie)


                if col != "Suivi des sauts" and lissage > 1:

                    serie = (
                        serie
                        .rolling(
                            window=lissage,
                            min_periods=1
                        )
                        .mean()
                    )


                ax.plot(
                    serie.index,
                    serie.values,
                    marker="o",
                    label=var
                )


    # =========================
    # FORMAT GRAPHIQUE
    # =========================

    ax.set_title(
        "Evolution des variables biologiques"
    )


    if "Suivi des sauts" in selected_vars:
        ax.set_ylabel("Nombre de sauts")
    else:
        ax.set_ylabel("Valeur moyenne")


    ax.grid(True)


    ax.legend()



    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%d/%m/%y")
    )


    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator()
    )


    fig.autofmt_xdate(
        rotation=45
    )


    st.pyplot(fig)
# =========================
# RANKING BOUCS
# =========================

elif mode == "🏆 Ranking boucs":

    show_ranking(
        ranking_last10,
        ranking_year,
        ranking_alltime,
        current_year
    )
# =========================
# CALENDRIER
# =========================

elif mode == "📅 Calendrier":

    st.subheader("📅 Calendrier annuel des suivis")

    import calendar as cal

    # =========================
    # MAP COULEURS FIXES
    # =========================

    COLOR_MAP = {
        "FCO": "blue",
        "LNCR": "red",
        "CS": "green",
        "Pesée": "pink",
        "TUB": "yellow"
    }

    def normalize(x):
        return str(x).strip()

    def get_color_list(suivis):
        colors = []

        for s in suivis:
            s = normalize(s)

            if s in COLOR_MAP:
                colors.append(COLOR_MAP[s])
            else:
                colors.append("gray")

        # enlever doublons consécutifs
        cleaned = []
        for c in colors:
            if c not in cleaned:
                cleaned.append(c)

        return cleaned if cleaned else ["white"]

    # =========================
    # DATA CLEAN
    # =========================

    suivi_cols = ["Suivi 1", "Suivi 2", "Suivi 3", "Suivi 4"]
    existing_cols = [c for c in suivi_cols if c in df.columns]

    df_suivi = df.melt(
        id_vars=["Date"],
        value_vars=existing_cols,
        value_name="Suivi"
    )

    df_suivi["Suivi"] = df_suivi["Suivi"].astype(str).str.strip()
    df_suivi = df_suivi[df_suivi["Suivi"].notna()]
    df_suivi = df_suivi[df_suivi["Suivi"] != ""]

    daily = df_suivi.groupby("Date")["Suivi"].apply(list).reset_index()

    color_map = {
        row["Date"].date(): get_color_list(row["Suivi"])
        for _, row in daily.iterrows()
    }

    # =========================
    # LÉGENDE (IDENTIQUE À TON CODE)
    # =========================

    st.markdown("### Légende")

    cols = st.columns(len(COLOR_MAP))

    for col, (label, color) in zip(cols, COLOR_MAP.items()):
        with col:
            st.markdown(
                f"""
                <div style='display:flex;align-items:center;'>
                    <div style='width:18px;height:18px;background:{color};
                    border:1px solid black;margin-right:6px'></div>
                    {label}
                </div>
                """,
                unsafe_allow_html=True
            )

    # =========================
    # ANNÉE BASE
    # =========================

    base_year = df["Date"].dt.year.max()

    # A0, puis A-1 jusqu'à A-10
    years = [base_year - i for i in range(0, 11)]

    highlight_months = {1, 4, 5, 8, 9, 12}

    # =========================
    # FIGURES PAR ANNÉE
    # =========================

    for year in years:

        st.markdown(f"### 📅 Année {year}")

        fig, axes = plt.subplots(3, 4, figsize=(18, 10))
        axes = axes.flatten()

        for month in range(1, 13):

            ax = axes[month - 1]
            ax.set_title(cal.month_name[month])
            ax.axis("off")

            month_matrix = cal.monthcalendar(year, month)

            for i, week in enumerate(month_matrix):
                for j, day in enumerate(week):

                    if day == 0:
                        continue

                    d = pd.Timestamp(year, month, day).date()
                    colors = color_map.get(d, ["white"])

                    # case simple
                    if len(colors) == 1:
                        ax.add_patch(plt.Rectangle(
                            (j, -i), 1, 1,
                            facecolor=colors[0],
                            edgecolor="black",
                            lw=0.4
                        ))

                    # multi couleurs
                    else:
                        ax.add_patch(plt.Rectangle(
                            (j, -i), 1, 1,
                            facecolor="white",
                            edgecolor="black",
                            lw=0.4
                        ))

                        step = 1 / len(colors[:4])

                        for k, c in enumerate(colors[:4]):
                            ax.add_patch(plt.Rectangle(
                                (j + k * step, -i),
                                step, 1,
                                facecolor=c,
                                edgecolor="none"
                            ))

            ax.set_xlim(0, 7)
            ax.set_ylim(-6, 1)

            if month in highlight_months:
                ax.add_patch(plt.Rectangle(
                    (0, -6), 7, 7,
                    fill=False,
                    edgecolor="yellow",
                    linewidth=3
                ))

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
