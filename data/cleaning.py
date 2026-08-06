import pandas as pd


def clean_data(all_values):

    headers = all_values[1]
    rows = all_values[2:]

    df = pd.DataFrame(
        rows,
        columns=headers
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce",
        dayfirst=True
    )

    df["Comportement"] = pd.to_numeric(
        df["Comportement"],
        errors="coerce"
    )

    df["Score"] = pd.to_numeric(
        df["Score"]
        .astype(str)
        .str.replace(",", "."),
        errors="coerce"
    )

    df["Succes"] = (
        df["Comportement"]
        .isin([2,3,4])
        .astype(int)
    )

    df["Code animal"] = (
        df["Code animal"]
        .astype(str)
        .str.strip()
    )

    df = df.dropna(
        subset=["Date"]
    )

    return df
