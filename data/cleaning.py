import pandas as pd


def clean_data(all_values):

    headers = all_values[1]
    rows = all_values[2:]

    df = pd.DataFrame(
        rows,
        columns=headers
    )

    # Nettoyage des noms de colonnes
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    # =========================
    # DATE
    # =========================

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
        dayfirst=True
    )

    # =========================
    # COMPORTEMENT
    # =========================

    df["Comportement"] = pd.to_numeric(
        df["Comportement"],
        errors="coerce"
    )

    # =========================
    # SCORE
    # =========================

    if "Score" in df.columns:

        df["Score"] = pd.to_numeric(
            df["Score"]
            .astype(str)
            .str.replace(",", ".", regex=False),
            errors="coerce"
        )

    # =========================
    # SUCCES
    # =========================

    df["Succes"] = (
        df["Comportement"]
        .isin([2, 3, 4])
        .astype(int)
    )

    # =========================
    # CODE ANIMAL
    # =========================

    df["Code animal"] = (
        df["Code animal"]
        .astype(str)
        .str.strip()
    )

    # =========================
    # POIDS
    # =========================

    if "Valeure Pesée" in df.columns:

        df["Valeure Pesée"] = pd.to_numeric(
            df["Valeure Pesée"]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
            .str.replace("kg", "", regex=False)
            .str.strip(),
            errors="coerce"
        )

    # =========================
    # CS
    # =========================

    if "Valeur CS" in df.columns:

        df["Valeur CS"] = pd.to_numeric(
            df["Valeur CS"]
            .astype(str)
            .str.strip()
            .str.replace(",", ".", regex=False)
            .str.replace("cm", "", regex=False)
            .str.strip(),
            errors="coerce"
        )

    # =========================
    # DATE VALIDE
    # =========================

    df = df.dropna(
        subset=["Date"]
    )

    return df
