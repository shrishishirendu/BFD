# Bihar Foundation Invitation Mailer

Internal Streamlit web application for personalised invitation preview and sending via Microsoft 365.

## Features

- Upload invitee spreadsheets (.xlsx, .xls, .csv) with Name and Email columns
- Upload PDF invitation templates with `{{ placeholder }}` syntax
- Validate spreadsheet rows (missing data, invalid emails, duplicates)
- Preview personalised invitations with merged placeholders
- Download personalised PDF invitations
- Send emails via Microsoft Graph (single or bulk)
- Attach personalised PDF to each email
- Full send log with CSV export
- Test mode for safe dry runs
- Global event settings (name, date, venue, RSVP link, etc.)

## Architecture

```
streamlit_app/
  app.py                          # Main Streamlit UI
  config.py                       # Configuration from env vars
  services/
    auth_service.py               # MSAL OAuth 2.0 delegated auth
    template_service.py           # PDF template merging
    email_service.py              # Microsoft Graph sendMail
    validation_service.py         # Spreadsheet and placeholder validation
    log_service.py                # CSV/JSON send logging
  utils/
    dataframe_utils.py            # DataFrame loading and normalisation
    placeholder_utils.py          # Placeholder extraction and merging
    file_utils.py                 # File system helpers
  tests/                          # pytest unit tests
  output/generated_docs/          # Generated personalised PDFs
  output/logs/                    # Send logs
```

## Prerequisites

- Python 3.10+
- A Microsoft Entra ID (Azure AD) app registration

### Microsoft Entra App Registration

1. Go to [Azure Portal](https://portal.azure.com) > Microsoft Entra ID > App registrations
2. Create a new registration:
   - **Name**: Bihar Foundation Invitation Mailer
   - **Supported account types**: Single tenant
   - **Redirect URI**: Web — `http://localhost:8501`
3. Under **Certificates & secrets**, create a new client secret
4. Under **API permissions**, add:
   - Microsoft Graph > Delegated > `User.Read`
   - Microsoft Graph > Delegated > `Mail.Send`
   - Grant admin consent
5. The signed-in user must have **Send As** or **Send on Behalf** rights for `connect@biharfoundation.org.au` if using a shared mailbox

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>
AZURE_REDIRECT_URI=http://localhost:8501
```

See `.env.example` for all available settings.

## How to Run Locally

```bash
cd streamlit_app
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Edit .env with your Azure credentials
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## How to Use

1. **Sign in** with your Microsoft 365 account using the sidebar link
2. **Upload** an invitee spreadsheet with Name and Email columns
3. **Upload** a PDF invitation template with `{{ placeholders }}`
4. **Fill in** global event settings in the sidebar (event name, date, venue, etc.)
5. **Review** the validation summary; fix any invalid rows in your spreadsheet
6. **Select** a recipient and click **Preview** to see the merged invitation
7. **Download** the personalised PDF if needed
8. **Compose** the email subject and body
9. **Send Selected** to email one recipient, or **Send All** for bulk send
10. **Download** the send log CSV for your records

## Testing

```bash
cd streamlit_app
pip install -r requirements.txt
pytest tests/ -v
```

## Known Limitations

- PDF placeholder merging works by extracting text and creating an overlay. For complex layouts, a form-fillable PDF template with dedicated fields would produce better results.
- The app stores tokens in Streamlit session state, which is cleared on page refresh.
- Bulk send uses a configurable delay between emails (default 1 second) to avoid throttling.
