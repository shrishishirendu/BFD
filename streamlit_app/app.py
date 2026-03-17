"""
Bihar Foundation Invitation Mailer
Main Streamlit application.
"""

import sys
import time
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure the app directory is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    APP_TITLE,
    DEFAULT_SUBJECT,
    DEFAULT_SENDER,
    ENABLE_BULK_SEND,
    ENABLE_ATTACHMENT,
    BULK_SEND_DELAY,
    TEST_MODE,
    GENERATED_DOCS_DIR,
)
from services.auth_service import (
    get_auth_url,
    acquire_token_by_code,
    get_access_token_silent,
    get_current_user,
    is_authenticated,
    sign_out,
    is_configured,
)
from services.validation_service import (
    validate_required_columns,
    validate_rows,
    get_validation_summary,
    get_valid_indices,
    check_placeholder_coverage,
)
from services.template_service import (
    get_template_placeholders,
    generate_preview_text,
    generate_personalised_pdf,
)
from services.email_service import (
    build_attachment,
    build_send_mail_payload,
    send_mail,
)
from services.log_service import (
    write_log_entry,
    get_log_dataframe,
    get_log_csv_bytes,
)
from utils.dataframe_utils import load_spreadsheet, row_to_merge_dict
from utils.file_utils import safe_filename

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

if TEST_MODE:
    st.warning("TEST MODE is enabled. All emails will be redirected to the configured test recipient.")

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
_defaults = {
    "df": None,
    "validation_df": None,
    "template_bytes": None,
    "template_placeholders": [],
    "send_log": [],
    "global_event": {},
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Sidebar: Authentication
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Authentication")

    if not is_configured():
        st.info(
            "Azure credentials are not configured. "
            "Set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET "
            "in your .env file or Streamlit secrets."
        )
    else:
        if is_authenticated():
            token = get_access_token_silent()
            if token:
                try:
                    user = get_current_user(token)
                    st.success(f"Signed in as **{user.get('displayName', '')}**")
                    st.caption(user.get("mail") or user.get("userPrincipalName", ""))
                except Exception as exc:
                    st.error(f"Could not fetch user info: {exc}")
            if st.button("Sign out"):
                sign_out()
                st.rerun()
        else:
            # Check for auth code in query params (OAuth callback)
            query_params = st.query_params
            auth_code = query_params.get("code")
            if auth_code:
                with st.spinner("Completing sign-in..."):
                    result = acquire_token_by_code(auth_code)
                if "access_token" in result:
                    st.success("Signed in successfully!")
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"Sign-in failed: {result.get('error_description', result.get('error', 'Unknown error'))}")
            else:
                auth_url = get_auth_url()
                st.markdown(f"[Sign in with Microsoft]({auth_url})")

    st.divider()
    st.caption(f"Sender: {DEFAULT_SENDER}")

# ---------------------------------------------------------------------------
# Sidebar: Global Event Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Event Settings")
    event_name = st.text_input("Event name", key="evt_name")
    event_date = st.text_input("Event date", key="evt_date")
    event_time = st.text_input("Event time", key="evt_time")
    venue = st.text_input("Venue", key="evt_venue")
    rsvp_link = st.text_input("RSVP link", key="evt_rsvp")
    contact_name = st.text_input("Contact name", key="evt_contact_name")
    contact_email = st.text_input("Contact email", key="evt_contact_email")
    signature_block = st.text_area("Signature block", key="evt_signature", height=80)

    st.session_state["global_event"] = {
        "event_name": event_name,
        "event_date": event_date,
        "event_time": event_time,
        "venue": venue,
        "rsvp_link": rsvp_link,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "signature_block": signature_block,
    }

# ---------------------------------------------------------------------------
# Main area: File Uploads
# ---------------------------------------------------------------------------
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    st.subheader("Invitee Spreadsheet")
    uploaded_spreadsheet = st.file_uploader(
        "Upload .xlsx, .xls, or .csv",
        type=["xlsx", "xls", "csv"],
        key="spreadsheet_upload",
    )
    if uploaded_spreadsheet:
        try:
            st.session_state["df"] = load_spreadsheet(uploaded_spreadsheet)
            st.success(f"Loaded {len(st.session_state['df'])} rows.")
        except Exception as exc:
            st.error(f"Error reading spreadsheet: {exc}")
            st.session_state["df"] = None

with col_upload2:
    st.subheader("PDF Invitation Template")
    uploaded_template = st.file_uploader(
        "Upload .pdf template with {{ placeholders }}",
        type=["pdf"],
        key="template_upload",
    )
    if uploaded_template:
        st.session_state["template_bytes"] = uploaded_template.read()
        placeholders = get_template_placeholders(st.session_state["template_bytes"])
        st.session_state["template_placeholders"] = placeholders
        if placeholders:
            st.info(f"Detected placeholders: {', '.join(placeholders)}")
        else:
            st.warning("No placeholders detected in the template. The PDF may not contain extractable text placeholders.")

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
df = st.session_state["df"]

if df is not None:
    st.divider()
    st.subheader("Validation")

    missing_cols = validate_required_columns(df)
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}. Please upload a spreadsheet with 'Name' and 'Email' columns.")
    else:
        validation_df = validate_rows(df)
        st.session_state["validation_df"] = validation_df
        summary = get_validation_summary(validation_df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Rows", summary["total"])
        c2.metric("Valid", summary["valid"])
        c3.metric("Invalid", summary["invalid"])
        c4.metric("Duplicates", summary["duplicates"])

        invalid_rows = validation_df[validation_df["status"] == "Invalid"]
        if not invalid_rows.empty:
            with st.expander(f"Show {len(invalid_rows)} invalid row(s)", expanded=False):
                st.dataframe(invalid_rows, use_container_width=True)

# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------
if (
    df is not None
    and st.session_state.get("validation_df") is not None
    and st.session_state.get("template_bytes") is not None
):
    st.divider()
    st.subheader("Preview Invitation")

    validation_df = st.session_state["validation_df"]
    valid_indices = get_valid_indices(df, validation_df)

    if not valid_indices:
        st.warning("No valid recipients to preview.")
    else:
        valid_rows = df.iloc[valid_indices]
        recipient_options = [
            f"{row.get('Name', row.get('name', ''))} ({row.get('Email', row.get('email', ''))})"
            for _, row in valid_rows.iterrows()
        ]

        selected_label = st.selectbox("Select recipient", recipient_options)
        selected_idx = valid_indices[recipient_options.index(selected_label)]
        selected_row = df.iloc[selected_idx]

        # Build merge context
        merge_dict = row_to_merge_dict(selected_row)
        global_event = {k: v for k, v in st.session_state["global_event"].items() if v}
        context = {**global_event, **merge_dict}

        # Check placeholder coverage
        template_placeholders = st.session_state["template_placeholders"]
        missing_ph = check_placeholder_coverage(
            template_placeholders,
            list(merge_dict.keys()),
            list(global_event.keys()),
        )
        if missing_ph:
            st.warning(f"Missing values for template placeholders: {', '.join(missing_ph)}")

        if st.button("Preview"):
            with st.spinner("Generating preview..."):
                preview_text = generate_preview_text(
                    st.session_state["template_bytes"], context
                )
                st.session_state["preview_text"] = preview_text
                st.session_state["selected_idx"] = selected_idx

        if "preview_text" in st.session_state:
            st.text_area(
                "Merged invitation text",
                value=st.session_state["preview_text"],
                height=300,
                disabled=True,
            )

            # Generate and offer PDF download
            if st.button("Download Personalised PDF"):
                with st.spinner("Generating PDF..."):
                    pdf_bytes, pdf_path = generate_personalised_pdf(
                        st.session_state["template_bytes"],
                        context,
                        merge_dict.get("name", "recipient"),
                    )
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=safe_filename(merge_dict.get("name", "invitation")),
                        mime="application/pdf",
                    )
                    st.caption(f"Also saved to: {pdf_path}")

# ---------------------------------------------------------------------------
# Email Composer & Send
# ---------------------------------------------------------------------------
if (
    df is not None
    and st.session_state.get("template_bytes") is not None
    and st.session_state.get("validation_df") is not None
):
    st.divider()
    st.subheader("Email Composer")

    email_subject = st.text_input("Subject", value=DEFAULT_SUBJECT)
    email_body = st.text_area(
        "Email body (HTML supported)",
        value="<p>Dear {{ name }},</p><p>Please find your personalised invitation attached.</p><p>Warm regards,<br>Bihar Foundation</p>",
        height=120,
    )
    attach_pdf = st.checkbox("Attach personalised PDF", value=ENABLE_ATTACHMENT)

    validation_df = st.session_state["validation_df"]
    valid_indices = get_valid_indices(df, validation_df)

    # --- Single Send ---
    st.subheader("Send to Selected Recipient")
    if "selected_idx" in st.session_state:
        sel_row = df.iloc[st.session_state["selected_idx"]]
        sel_merge = row_to_merge_dict(sel_row)
        global_event = {k: v for k, v in st.session_state["global_event"].items() if v}
        sel_context = {**global_event, **sel_merge}
        sel_name = sel_merge.get("name", "")
        sel_email = sel_merge.get("email", "")

        st.write(f"Recipient: **{sel_name}** ({sel_email})")

        if st.button("Send Selected", type="primary"):
            if not is_authenticated():
                st.error("Please sign in with Microsoft before sending.")
            else:
                with st.spinner(f"Sending to {sel_email}..."):
                    # Generate PDF
                    pdf_bytes, pdf_path = generate_personalised_pdf(
                        st.session_state["template_bytes"],
                        sel_context,
                        sel_name,
                    )
                    # Build body with placeholders merged
                    from utils.placeholder_utils import merge_text_with_context
                    merged_body = merge_text_with_context(email_body, sel_context)

                    attachment = None
                    if attach_pdf:
                        attachment = build_attachment(
                            safe_filename(sel_name), pdf_bytes
                        )

                    payload = build_send_mail_payload(
                        sel_email, email_subject, merged_body, attachment
                    )
                    token = get_access_token_silent()
                    result = send_mail(token, payload)

                    status = "Sent" if result["success"] else "Failed"
                    write_log_entry(
                        sel_name, sel_email, status,
                        error_message=result.get("error", ""),
                        message_id=result.get("message_id", ""),
                        pdf_path=str(pdf_path),
                    )
                    if result["success"]:
                        st.success(f"Email sent to {sel_email}")
                    else:
                        st.error(f"Failed: {result['error']}")
    else:
        st.info("Select a recipient and click Preview above to enable single send.")

    # --- Bulk Send ---
    if ENABLE_BULK_SEND and valid_indices:
        st.divider()
        st.subheader("Bulk Send")
        st.write(f"Send to all **{len(valid_indices)}** valid recipients.")

        confirm_bulk = st.checkbox(
            "I confirm I want to send emails to all valid recipients",
            key="bulk_confirm",
        )

        if st.button("Send All", type="primary", disabled=not confirm_bulk):
            if not is_authenticated():
                st.error("Please sign in with Microsoft before sending.")
            else:
                token = get_access_token_silent()
                progress = st.progress(0, text="Starting bulk send...")
                success_count = 0
                fail_count = 0
                total = len(valid_indices)

                from utils.placeholder_utils import merge_text_with_context as _merge

                for i, idx in enumerate(valid_indices):
                    row = df.iloc[idx]
                    merge = row_to_merge_dict(row)
                    global_ev = {k: v for k, v in st.session_state["global_event"].items() if v}
                    ctx = {**global_ev, **merge}
                    name = merge.get("name", "")
                    email = merge.get("email", "")

                    try:
                        pdf_bytes, pdf_path = generate_personalised_pdf(
                            st.session_state["template_bytes"], ctx, name
                        )
                    except Exception as exc:
                        write_log_entry(name, email, "Failed", error_message=f"PDF generation error: {exc}")
                        fail_count += 1
                        progress.progress((i + 1) / total, text=f"Failed PDF for {name}")
                        continue

                    merged_body = _merge(email_body, ctx)
                    attachment = None
                    if attach_pdf:
                        attachment = build_attachment(safe_filename(name), pdf_bytes)

                    payload = build_send_mail_payload(
                        email, email_subject, merged_body, attachment
                    )
                    result = send_mail(token, payload)

                    status = "Sent" if result["success"] else "Failed"
                    write_log_entry(
                        name, email, status,
                        error_message=result.get("error", ""),
                        message_id=result.get("message_id", ""),
                        pdf_path=str(pdf_path),
                    )

                    if result["success"]:
                        success_count += 1
                    else:
                        fail_count += 1

                    progress.progress(
                        (i + 1) / total,
                        text=f"Processed {i + 1}/{total} — {name}",
                    )

                    if BULK_SEND_DELAY > 0 and i < total - 1:
                        time.sleep(BULK_SEND_DELAY)

                progress.empty()
                st.success(f"Bulk send complete: {success_count} sent, {fail_count} failed.")

# ---------------------------------------------------------------------------
# Send Log
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Send Log")

log_df = get_log_dataframe()
if log_df.empty:
    st.info("No send attempts logged yet.")
else:
    st.dataframe(log_df, use_container_width=True)
    csv_bytes = get_log_csv_bytes()
    if csv_bytes:
        st.download_button(
            label="Download Send Log (CSV)",
            data=csv_bytes,
            file_name="send_log.csv",
            mime="text/csv",
        )
