# EduCraft Solutions — Full-Stack Website

A complete Flask-based education consultancy website with:
- Public website (Home, About, Services, Study Abroad, Contact, Enquiry)
- Google OAuth2 login
- Email/Password login with OTP verification via SMTP
- Client & Admin login roles
- Admin dashboard (messages, enquiries, users, Excel export, reply)
- Contact form → SQLite DB + Excel file + Admin email alert
- Overseas Enquiry form → DB + Excel + Admin email alert
- AI Chatbot (EduBot) in the bottom-right corner

---

## Folder Structure

```
educraft_website/
├── app.py                          ← Flask backend (all routes & logic)
├── requirements.txt
├── .env.example                    ← Copy to .env and fill credentials
├── README.md
├── instance/
│   └── educraft.db                 ← SQLite DB (auto-created on first run)
├── data/
│   └── educraft_contacts.xlsx      ← Excel export (auto-generated)
├── static/
│   ├── css/main.css
│   └── js/main.js
└── templates/
    ├── base.html                   ← Navbar, footer, chatbot (shared)
    ├── home.html
    ├── login.html                  ← Client + Admin login with role toggle
    ├── signup.html                 ← Registration form
    ├── verify_otp.html             ← OTP verification
    ├── overseas.html               ← Study Abroad page
    ├── enquiry.html                ← Free Enquiry form
    ├── services.html
    ├── about.html
    ├── contact.html
    └── admin/
        ├── base_admin.html         ← Admin sidebar layout
        ├── dashboard.html          ← Stats + recent activity
        ├── messages.html           ← Contact messages + reply
        ├── enquiries.html          ← Overseas enquiries table
        └── users.html              ← Registered users management
```

---

## Quick Start in VS Code

### Step 1 — Open folder
```
File → Open Folder → educraft_website
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
```

### Step 3 — Activate
```bash
# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 — Configure environment
```bash
# Copy the example file
cp .env.example .env

# Then open .env and fill in your real values (see below)
```

### Step 6 — Run
```bash
python app.py
```

Open → http://127.0.0.1:5000

---

## Configuration (.env)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Random secret string for Flask sessions |
| `SMTP_HOST` | SMTP server (default: smtp.gmail.com) |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASS` | Gmail App Password (16 chars, no spaces) |
| `ADMIN_EMAIL` | Email to receive contact/enquiry alerts |
| `ADMIN_EMAIL_LOGIN` | Admin login email (default: admin@educraft.com) |
| `ADMIN_PASSWORD` | Admin login password (default: Admin@1234) |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |

---

## Gmail App Password (SMTP)

1. Go to your Google Account → **Security**
2. Enable **2-Step Verification**
3. Scroll to **App passwords** → Create one for "Mail"
4. Copy the 16-character password → paste as `SMTP_PASS` in `.env`

> **Dev mode:** If SMTP is not configured, OTP is printed to the VS Code terminal console.

---

## Google OAuth Setup

1. Go to https://console.cloud.google.com
2. Create a new project
3. APIs & Services → **Credentials** → Create OAuth 2.0 Client ID
4. Application type: **Web application**
5. Add Authorized redirect URI:
   ```
   http://localhost:5000/auth/google/callback
   ```
6. Copy **Client ID** and **Client Secret** → paste into `.env`

> If `GOOGLE_CLIENT_ID` is empty, Google login shows a "not configured" message and falls back to email login gracefully.

---

## Admin Access

| Field | Value |
|---|---|
| URL | http://127.0.0.1:5000/login |
| Role | Select **Admin** tab |
| Email | `admin@educraft.com` |
| Password | `Admin@1234` |

Change these in `.env` before going live.

**Admin Panel features:**
- Dashboard with stats cards
- View & reply to all contact messages
- View & delete overseas enquiries
- Manage (view/delete) registered users
- Download full Excel report (3 sheets: Messages, Enquiries, Users)

---

## Key Routes

| Route | Description |
|---|---|
| `/` | Home page |
| `/login` | Login (Client & Admin) |
| `/signup` | Registration |
| `/verify-otp` | OTP verification after signup |
| `/auth/google` | Google OAuth login |
| `/overseas` | Study Abroad page |
| `/enquiry` | Free Enquiry form |
| `/services` | Services page |
| `/about` | About Us |
| `/contact` | Contact form |
| `/admin` | Admin dashboard |
| `/admin/messages` | Contact messages |
| `/admin/enquiries` | Overseas enquiries |
| `/admin/users` | Registered users |
| `/admin/download-excel` | Download Excel report |

---

## For Production

- Set `DEBUG=False` in `app.py`
- Use PostgreSQL instead of SQLite (change `SQLALCHEMY_DATABASE_URI`)
- Use a real WSGI server (Gunicorn / uWSGI)
- Set `https://yourdomain.com/auth/google/callback` in Google Console
- Store `SECRET_KEY` as a proper random 64-char string
