"""
Validation service for invitee spreadsheets and template placeholders.
"""

import pandas as pd
from email_validator import validate_email, EmailNotValidError

from utils.dataframe_utils import canonical_name, get_column_mapping
from config import REQUIRED_COLUMNS


def validate_required_columns(df: pd.DataFrame) -> list[str]:
    """
    Check that all required columns are present.
    Returns a list of missing column names (empty if all present).
    """
    col_map = get_column_mapping(df)
    missing = [rc for rc in REQUIRED_COLUMNS if rc not in col_map]
    return missing


def validate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate each row for name, email, and duplicates.
    Returns a DataFrame with columns: row_number, name, email, status, errors.
    """
    col_map = get_column_mapping(df)
    name_col = col_map.get("name")
    email_col = col_map.get("email")

    results = []
    seen_emails: dict[str, int] = {}

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed + header row
        errors = []
        name_val = str(row.get(name_col, "")).strip() if name_col else ""
        email_val = str(row.get(email_col, "")).strip() if email_col else ""

        if not name_val:
            errors.append("Name is empty")

        if not email_val:
            errors.append("Email is empty")
        else:
            try:
                validate_email(email_val, check_deliverability=False)
            except EmailNotValidError as e:
                errors.append(f"Invalid email: {e}")

            lower_email = email_val.lower()
            if lower_email in seen_emails:
                errors.append(f"Duplicate email (first seen row {seen_emails[lower_email]})")
            else:
                seen_emails[lower_email] = row_num

        status = "Valid" if not errors else "Invalid"
        results.append({
            "row_number": row_num,
            "name": name_val,
            "email": email_val,
            "status": status,
            "errors": "; ".join(errors) if errors else "",
        })

    return pd.DataFrame(results)


def get_validation_summary(validation_df: pd.DataFrame) -> dict:
    """Return counts for total, valid, invalid, and duplicate rows."""
    total = len(validation_df)
    valid = len(validation_df[validation_df["status"] == "Valid"])
    invalid = total - valid
    duplicates = len(validation_df[
        validation_df["errors"].str.contains("Duplicate", na=False)
    ])
    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "duplicates": duplicates,
    }


def get_valid_indices(df: pd.DataFrame, validation_df: pd.DataFrame) -> list[int]:
    """Return original DataFrame indices for valid rows."""
    valid_rows = validation_df[validation_df["status"] == "Valid"]
    # row_number is 2-indexed (1-based + header), convert back to 0-based df index
    return [r - 2 for r in valid_rows["row_number"].tolist()]


def check_placeholder_coverage(
    template_placeholders: list[str],
    row_keys: list[str],
    global_keys: list[str],
) -> list[str]:
    """
    Check that every template placeholder has a matching key in either
    the row data or global event settings.
    Returns a list of unmatched placeholder names.
    """
    available = {k.lower() for k in row_keys} | {k.lower() for k in global_keys}
    return [p for p in template_placeholders if p.lower() not in available]
