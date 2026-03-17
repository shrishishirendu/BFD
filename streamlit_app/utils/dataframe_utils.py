"""
Utilities for loading and normalising invitee spreadsheets.
"""

import pandas as pd
import numpy as np


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace from column names and convert to lowercase canonical form."""
    df.columns = [col.strip() for col in df.columns]
    return df


def canonical_name(col: str) -> str:
    """Return the lowercase, stripped version of a column name."""
    return col.strip().lower().replace(" ", "_")


def get_column_mapping(df: pd.DataFrame) -> dict[str, str]:
    """Map canonical column names back to actual DataFrame column names."""
    return {canonical_name(col): col for col in df.columns}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Trim string whitespace and replace NaN with empty strings."""
    df = normalise_columns(df)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].fillna("").astype(str).str.strip()
        else:
            df[col] = df[col].fillna("")
    return df


def load_spreadsheet(file) -> pd.DataFrame:
    """
    Read an uploaded file (xlsx, xls, csv) into a cleaned DataFrame.
    Accepts a Streamlit UploadedFile or a file path string.
    """
    if isinstance(file, str):
        name = file
    else:
        name = file.name

    if name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file, engine="openpyxl")

    return clean_dataframe(df)


def row_to_merge_dict(row: pd.Series) -> dict[str, str]:
    """Convert a DataFrame row into a merge dictionary with lowercase keys."""
    return {canonical_name(k): str(v) for k, v in row.items()}
