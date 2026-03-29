# 📊 Google Sheets Live Data Setup Guide

This guide shows you how to connect EduCraft to Google Sheets so that
**contact messages, overseas enquiries, and user registrations
auto-update in real-time** whenever a form is submitted.

---

## What You'll Get

A Google Sheet with 3 tabs that update automatically:

| Sheet Tab | Updates When |
|---|---|
| **Contact Messages** | User submits Contact form |
| **Overseas Enquiries** | User submits Enquiry form |
| **Registered Users** | New user signs up |

---

## Step 1 — Create a Google Cloud Project

1. Go to → https://console.cloud.google.com
2. Click **"New Project"** → name it `EduCraft` → **Create**
3. Make sure this project is selected in the top menu

---

## Step 2 — Enable Required APIs

1. In the left menu: **APIs & Services → Library**
2. Search for and **Enable** both:
   - ✅ **Google Sheets API**
   - ✅ **Google Drive API**

---

## Step 3 — Create a Service Account

1. Go to: **APIs & Services → Credentials**
2. Click **"+ Create Credentials"** → **Service Account**
3. Fill in:
   - **Name**: `educraft-sheets`
   - **ID**: auto-filled
4. Click **Create and Continue** → **Done**

---

## Step 4 — Download JSON Key File

1. On the Credentials page, click your new service account
2. Go to the **Keys** tab
3. Click **Add Key → Create new key → JSON**
4. A `.json` file downloads automatically
5. **Rename it** to `gsheet_credentials.json`
6. **Place it** in your `educraft_website/` folder

```
educraft_website/
├── app.py
├── gsheet_credentials.json   ← place here
├── .env
...
```

> ⚠️ **NEVER commit this file to Git.** Add it to `.gitignore`.

---

## Step 5 — Create the Google Sheet

1. Go to → https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it: **`EduCraft Live Data`**
4. Copy its URL from the browser address bar

It looks like:
```
https://docs.google.com/spreadsheets/d/1BxiM.../edit#gid=0
```

---

## Step 6 — Share the Sheet with Your Service Account

1. Open `gsheet_credentials.json` in a text editor
2. Find the `"client_email"` field — it looks like:
   ```
   educraft-sheets@your-project.iam.gserviceaccount.com
   ```
3. In your Google Sheet, click **Share**
4. Paste that email address
5. Set permission to **Editor**
6. Click **Send** (ignore "can't notify" warning)

---

## Step 7 — Update Your .env File

Open `.env` and set:

```env
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
GSHEET_KEY_FILE=gsheet_credentials.json
GSHEET_NAME=EduCraft Live Data
```

Replace `YOUR_SHEET_ID` with the long ID from your Sheet URL.

---

## Step 8 — Install Dependencies & Test

```bash
pip install gspread google-auth
python app.py
```

Then:
1. Log in as Admin → go to Dashboard
2. Click **"Sync Now"** button
3. Open your Google Sheet — you should see the 3 tabs with data!

---

## How It Works After Setup

```
User submits form
       ↓
Flask saves to SQLite DB
       ↓
Sends SMTP email alert to projecthubpshiksha@gmail.com
       ↓
Calls sync_to_sheets() in background
       ↓
Google Sheet updates instantly (all 3 tabs)
       ↓
Admin clicks "Click to See Live Data" → Sheet opens
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `gsheet_credentials.json not found` | Place the file in the `educraft_website/` root folder |
| `403 Forbidden` | Make sure you shared the sheet with the service account email |
| `API not enabled` | Enable Google Sheets API and Google Drive API in Cloud Console |
| Sheet not updating | Click "Sync Now" in admin panel, or check Flask terminal for errors |
| `ModuleNotFoundError: gspread` | Run `pip install gspread google-auth` |

---

## Security Notes

- ✅ Add `gsheet_credentials.json` to `.gitignore`
- ✅ Add `.env` to `.gitignore`  
- ✅ Never share your service account key publicly
- ✅ The sheet is only accessible to you (Google account owner) and the service account

---

## .gitignore (add these lines)

```
.env
gsheet_credentials.json
instance/
data/
__pycache__/
*.pyc
venv/
```
