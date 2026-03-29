"""
EduCraft Solutions – Full Backend
──────────────────────────────────
- SQLite DB  (Users, ContactMessage, Enquiry)
- Google OAuth2 login
- Email/Password + OTP signup via SMTP
- Admin: projecthubpshiksha@gmail.com
- Contact/Enquiry → SMTP alert to admin
- Google Sheets real-time sync (gspread + service account)
- Admin dashboard – messages, enquiries, users
- "View Live Data" button → opens Google Sheet
"""

import os, random, string, smtplib, json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, session, jsonify, send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth

# ─────────────────────────────────────────────────
# APP CONFIG
# ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'educraft_super_secret_2024_change_me')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'educraft.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ── SMTP ──────────────────────────────────────────
SMTP_HOST   = os.environ.get('SMTP_HOST',   'smtp.gmail.com')
SMTP_PORT   = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER   = os.environ.get('SMTP_USER',   'projecthubpshiksha@gmail.com')
SMTP_PASS   = os.environ.get('SMTP_PASS',   'your_gmail_app_password_here')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'projecthubpshiksha@gmail.com')

# ── ADMIN LOGIN ───────────────────────────────────
ADMIN_EMAIL_LOGIN = os.environ.get('ADMIN_EMAIL_LOGIN', 'projecthubpshiksha@gmail.com')
ADMIN_PASSWORD    = os.environ.get('ADMIN_PASSWORD',    'Admin@1234')

# ── GOOGLE OAUTH ──────────────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID',     '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# ── GOOGLE SHEETS ─────────────────────────────────
GOOGLE_SHEET_URL = os.environ.get(
    'GOOGLE_SHEET_URL',
    'https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit'
)
GSHEET_KEY_FILE = os.environ.get(
    'GSHEET_KEY_FILE',
    os.path.join(BASE_DIR, 'gsheet_credentials.json')
)
GSHEET_NAME = os.environ.get('GSHEET_NAME', 'EduCraft Live Data')

OTP_EXPIRY_MINUTES = 10

db = SQLAlchemy(app)

# ─────────────────────────────────────────────────
# GOOGLE SHEETS HELPERS
# ─────────────────────────────────────────────────
def get_gsheet_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
        ]
        if not os.path.exists(GSHEET_KEY_FILE):
            return None
        creds  = Credentials.from_service_account_file(GSHEET_KEY_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        app.logger.warning(f'gspread not available: {e}')
        return None


def _sync_worksheet(sh, title, headers, rows, header_color=None):
    """Clear a worksheet and rewrite with headers + data with coloured header row."""
    try:
        ws = sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows=500, cols=len(headers))

    all_data = [headers] + rows
    ws.clear()
    ws.update('A1', all_data)

    try:
        import gspread.utils as gu
        end_cell = gu.rowcol_to_a1(1, len(headers))
        color = header_color or {'red': 0.78, 'green': 0.92, 'blue': 0.78}
        ws.format(f'A1:{end_cell}', {
            'textFormat': {
                'bold': True,
                'foregroundColor': {'red': 0.1, 'green': 0.1, 'blue': 0.1}
            },
            'backgroundColor': color,
            'horizontalAlignment': 'CENTER',
        })
    except Exception:
        pass


def sync_to_sheets():
    """Push all DB records to Google Sheets. Silent no-op if gspread not configured."""
    client = get_gsheet_client()
    if not client:
        return

    try:
        try:
            sh = client.open(GSHEET_NAME)
        except Exception:
            sh = client.create(GSHEET_NAME)
            sh.share(ADMIN_EMAIL, perm_type='user', role='writer')

        # Sheet 1: Contact Messages — light green header
        _sync_worksheet(
            sh, 'Contact Messages',
            ['#', 'Name', 'Email', 'Phone', 'Service Interested', 'Message', 'Submitted At', 'Read'],
            [
                [m.id, m.name, m.email, m.phone or '', m.service or '',
                 m.message or '', m.submitted_at.strftime('%d-%b-%Y %H:%M'),
                 'Yes' if m.is_read else 'No']
                for m in ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
            ],
            header_color={'red': 0.78, 'green': 0.92, 'blue': 0.78},
        )

        # Sheet 2: Overseas Enquiries — light blue header
        _sync_worksheet(
            sh, 'Overseas Enquiries',
            ['#', 'Name', 'Email', 'Phone', 'Country', 'Course/Level', 'Budget', 'Message', 'Submitted At'],
            [
                [e.id, e.name, e.email, e.phone or '', e.country or '',
                 e.course or '', e.budget or '', e.message or '',
                 e.submitted_at.strftime('%d-%b-%Y %H:%M')]
                for e in Enquiry.query.order_by(Enquiry.submitted_at.desc()).all()
            ],
            header_color={'red': 0.73, 'green': 0.87, 'blue': 0.98},
        )

        # Sheet 3: Registered Users — light yellow header
        _sync_worksheet(
            sh, 'Registered Users',
            ['#', 'Name', 'Email', 'Phone', 'Interest', 'Sign-up Via', 'Verified', 'Joined'],
            [
                [u.id, u.name, u.email, u.phone or '', u.interest or '',
                 u.provider, 'Yes' if u.is_verified else 'No',
                 u.created_at.strftime('%d-%b-%Y')]
                for u in User.query.filter(User.role != 'admin')
                                   .order_by(User.created_at.desc()).all()
            ],
            header_color={'red': 1.0, 'green': 0.95, 'blue': 0.70},
        )

    except Exception as e:
        app.logger.error(f'Google Sheets sync error: {e}')


# ─────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(200), unique=True, nullable=False)
    phone       = db.Column(db.String(20),  default='')
    password    = db.Column(db.String(256), default='')
    interest    = db.Column(db.String(100), default='')
    provider    = db.Column(db.String(20),  default='email')
    role        = db.Column(db.String(10),  default='member')
    status      = db.Column(db.String(20),  default='Pending')
    access_used = db.Column(db.Boolean,     default=False)
    is_verified = db.Column(db.Boolean,     default=False)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120))
    email        = db.Column(db.String(200))
    phone        = db.Column(db.String(20),  default='')
    service      = db.Column(db.String(100), default='')
    message      = db.Column(db.Text)
    file_path    = db.Column(db.String(255), default='')
    submitted_at = db.Column(db.DateTime,    default=datetime.utcnow)
    is_read      = db.Column(db.Boolean,     default=False)


class Purchase(db.Model):
    __tablename__ = 'purchases'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_name    = db.Column(db.String(100), default='')
    amount       = db.Column(db.Float,       default=0.0)
    status       = db.Column(db.String(20),  default='Completed')
    purchased_at = db.Column(db.DateTime,    default=datetime.utcnow)


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    client_name = db.Column(db.String(100))
    client_email = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    status = db.Column(db.String(50))
    progress = db.Column(db.Integer)
    start_date = db.Column(db.String(100))
    deadline = db.Column(db.String(100))
    tech_stack = db.Column(db.String(300))
    milestones = db.Column(db.Text)


class Enquiry(db.Model):
    __tablename__ = 'enquiries'
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(120))
    email        = db.Column(db.String(200))
    phone        = db.Column(db.String(20),  default='')
    country      = db.Column(db.String(80),  default='')
    course       = db.Column(db.String(120), default='')
    budget       = db.Column(db.String(80),  default='')
    message      = db.Column(db.Text,        default='')
    submitted_at = db.Column(db.DateTime,    default=datetime.utcnow)
    is_read      = db.Column(db.Boolean,     default=False)


# ─────────────────────────────────────────────────
# DB INIT + SEED ADMIN
# ─────────────────────────────────────────────────
os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email=ADMIN_EMAIL_LOGIN).first():
        db.session.add(User(
            name        = 'Admin',
            email       = ADMIN_EMAIL_LOGIN,
            password    = generate_password_hash(ADMIN_PASSWORD),
            role        = 'admin',
            is_verified = True,
            provider    = 'email',
        ))
        db.session.commit()


# ─────────────────────────────────────────────────
# OAUTH
# ─────────────────────────────────────────────────
oauth = OAuth(app)
google_oauth = oauth.register(
    name          = 'google',
    client_id     = GOOGLE_CLIENT_ID,
    client_secret = GOOGLE_CLIENT_SECRET,
    server_metadata_url = 'https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs = {'scope': 'openid email profile'},
)


# ─────────────────────────────────────────────────
# EMAIL HELPERS
# ─────────────────────────────────────────────────
def send_email(to_addr, subject, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'EduCraft Solutions <{SMTP_USER}>'
        msg['To']      = to_addr
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(SMTP_USER, to_addr, msg.as_string())
        return True
    except Exception as e:
        app.logger.error(f'[SMTP ERROR] {e}')
        return False


def _email_wrapper(title_color, icon, title, rows_html, cta_url=None, cta_label=None):
    cta = ''
    if cta_url and cta_label:
        cta = f"""
        <div style="text-align:center;margin:28px 0">
          <a href="{cta_url}" style="background:#1a3c6e;color:#fff;padding:12px 28px;
             border-radius:8px;text-decoration:none;font-weight:600;font-size:.9rem">{cta_label}</a>
        </div>"""
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;margin:auto;background:#fff;
                border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
      <div style="background:{title_color};padding:22px 28px;display:flex;align-items:center">
        <span style="font-size:1.6rem;margin-right:12px">{icon}</span>
        <div>
          <div style="color:#fff;font-size:1.1rem;font-weight:700">{title}</div>
          <div style="color:rgba(255,255,255,.75);font-size:.78rem">
            EduCraft Solutions · {datetime.now().strftime('%d %b %Y, %I:%M %p')}</div>
        </div>
      </div>
      <div style="padding:24px 28px">
        <table style="width:100%;border-collapse:collapse;font-size:.88rem">
          {rows_html}
        </table>
        {cta}
      </div>
      <div style="background:#f4f7fb;padding:14px 28px;text-align:center;
                  font-size:.73rem;color:#9aa5b4">
        EduCraft Solutions &nbsp;·&nbsp; 1/191 Subhash Nagar, New Delhi – 110027
        &nbsp;·&nbsp; +91 9821693299
      </div>
    </div>"""


def _row(label, value, alt=False):
    bg = 'background:#f4f7fb;' if alt else ''
    return f"""
    <tr style="{bg}">
      <td style="padding:9px 12px;color:#5a6878;width:150px;font-weight:600">{label}</td>
      <td style="padding:9px 12px;color:#1a2332">{value}</td>
    </tr>"""


def send_otp_email(to_addr, name, otp):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;background:#fff;
                border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
      <div style="background:#1a3c6e;padding:22px 28px">
        <div style="color:#fff;font-size:1.1rem;font-weight:700">EduCraft Solutions</div>
        <div style="color:rgba(255,255,255,.75);font-size:.78rem">Email Verification</div>
      </div>
      <div style="padding:28px">
        <p style="color:#1a2332;margin:0 0 16px">Hi <strong>{name}</strong>,</p>
        <p style="color:#5a6878;margin:0 0 24px">
          Use the OTP below to verify your EduCraft account.
          It expires in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
        </p>
        <div style="text-align:center;margin:24px 0">
          <span style="background:#1a3c6e;color:#fff;font-size:2rem;font-weight:700;
                       letter-spacing:10px;padding:14px 30px;border-radius:10px;
                       display:inline-block">{otp}</span>
        </div>
        <p style="color:#9aa5b4;font-size:.78rem;text-align:center">
          Do not share this OTP with anyone.
        </p>
      </div>
      <div style="background:#f4f7fb;padding:12px 28px;text-align:center;
                  font-size:.72rem;color:#9aa5b4">
        EduCraft Solutions · 1/191 Subhash Nagar, New Delhi
      </div>
    </div>"""
    return send_email(to_addr, '🔐 Your EduCraft OTP Verification Code', html)


def send_contact_alert_email(cm):
    doc_row = _row('Attachment', f'<a href="http://localhost:5000/uploads/{cm.file_path}" style="color:#0097a7">View Document</a>', alt=False) if cm.file_path else ''
    rows = (
        _row('Name',     cm.name) +
        _row('Email',    f'<a href="mailto:{cm.email}" style="color:#0097a7">{cm.email}</a>', alt=True) +
        _row('Phone',    cm.phone or '—') +
        _row('Service',  f'<span style="background:#e8f4f8;color:#0097a7;padding:2px 10px;'
                         f'border-radius:50px;font-size:.8rem">{cm.service}</span>' if cm.service else '—', alt=True) +
        _row('Message',  cm.message) +
        doc_row +
        _row('Received', cm.submitted_at.strftime('%d %b %Y, %I:%M %p'), alt=True)
    )
    body = _email_wrapper(
        title_color = '#1a3c6e',
        icon        = '📩',
        title       = f'New Contact Message from {cm.name}',
        rows_html   = rows,
        cta_url     = 'http://localhost:5000/admin/messages',
        cta_label   = '→ View in Admin Panel',
    )
    send_email(ADMIN_EMAIL, f'📩 New Contact: {cm.name} – EduCraft Website', body)


def send_enquiry_alert_email(enq):
    rows = (
        _row('Name',    enq.name) +
        _row('Email',   f'<a href="mailto:{enq.email}" style="color:#0097a7">{enq.email}</a>', alt=True) +
        _row('Phone',   enq.phone or '—') +
        _row('Country', f'<strong>{enq.country}</strong>' if enq.country else '—', alt=True) +
        _row('Course',  enq.course or '—') +
        _row('Budget',  f'<span style="background:#fff8e8;color:#b7791f;padding:2px 10px;'
                        f'border-radius:50px;font-size:.8rem">{enq.budget}</span>' if enq.budget else '—', alt=True) +
        _row('Message', enq.message or '—')
    )
    body = _email_wrapper(
        title_color = '#0097a7',
        icon        = '🌍',
        title       = f'New Overseas Enquiry from {enq.name}',
        rows_html   = rows,
        cta_url     = 'http://localhost:5000/admin/enquiries',
        cta_label   = '→ View in Admin Panel',
    )
    send_email(ADMIN_EMAIL, f'🌍 New Overseas Enquiry: {enq.name} – EduCraft', body)


def send_new_user_alert_email(user):
    rows = (
        _row('Name',     user.name) +
        _row('Email',    f'<a href="mailto:{user.email}" style="color:#0097a7">{user.email}</a>', alt=True) +
        _row('Phone',    user.phone or '—') +
        _row('Interest', user.interest or '—', alt=True) +
        _row('Signed up via', user.provider.capitalize()) +
        _row('Joined',   user.created_at.strftime('%d %b %Y, %I:%M %p'), alt=True)
    )
    body = _email_wrapper(
        title_color = '#27ae60',
        icon        = '👤',
        title       = f'New User Registered: {user.name}',
        rows_html   = rows,
        cta_url     = 'http://localhost:5000/admin/users',
        cta_label   = '→ View All Users',
    )
    send_email(ADMIN_EMAIL, f'👤 New Registration: {user.name} – EduCraft', body)


# ─────────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        uid = session.get('user_id')
        role = session.get('role')
        if not uid or role == 'guest':
            flash('Please login to continue.', 'error')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrapped


def admin_required(f):
    @wraps(f)
    def wrapped(*a, **kw):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return wrapped


# ─────────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')



# ─────────────────────────────────────────────────
# CONTACT FORM
# ─────────────────────────────────────────────────
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        file = request.files.get('document')
        saved_file_name = ''
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            saved_file_name = filename

        cm = ContactMessage(
            name    = request.form.get('name',    '').strip(),
            email   = request.form.get('email',   '').strip(),
            phone   = request.form.get('phone',   '').strip(),
            service = request.form.get('service', '').strip(),
            message = request.form.get('message', '').strip(),
            file_path = saved_file_name
        )
        db.session.add(cm)
        db.session.commit()
        send_contact_alert_email(cm)
        sync_to_sheets()
        flash('Thank you! We received your message and will contact you within 24 hours.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')



# ─────────────────────────────────────────────────
# AUTH – SIGNUP
# ─────────────────────────────────────────────────
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name     = request.form.get('name',             '').strip()
        email    = request.form.get('email',            '').strip().lower()
        phone    = request.form.get('phone',            '').strip()
        interest = request.form.get('interest',         '').strip()
        password = request.form.get('password',         '')
        confirm  = request.form.get('confirm_password', '')

        if not all([name, email, password]):
            flash('Please fill all required fields.', 'error')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return render_template('signup.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('signup.html')
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')

        otp = generate_otp()
        session['pending_user'] = {
            'name': name, 'email': email, 'phone': phone,
            'interest': interest,
            'password': generate_password_hash(password),
            'otp': otp,
            'expires': (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat(),
        }

        sent = send_otp_email(email, name, otp)
        if not sent:
            print(f'\n[DEV MODE] OTP for {email} → {otp}\n')
        flash(f'OTP sent to {email}. Check your inbox.', 'info')
        return redirect(url_for('verify_otp'))
    return render_template('signup.html')


# ─────────────────────────────────────────────────
# AUTH – VERIFY OTP
# ─────────────────────────────────────────────────
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    pending = session.get('pending_user')
    if not pending:
        flash('Session expired. Please sign up again.', 'error')
        return redirect(url_for('signup'))

    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        expires = datetime.fromisoformat(pending['expires'])

        if datetime.utcnow() > expires:
            session.pop('pending_user', None)
            flash('OTP expired. Please sign up again.', 'error')
            return redirect(url_for('signup'))

        if entered != pending['otp']:
            flash('Incorrect OTP. Please try again.', 'error')
            return render_template('verify_otp.html', email=pending['email'])

        user = User(
            name        = pending['name'],
            email       = pending['email'],
            phone       = pending['phone'],
            interest    = pending['interest'],
            password    = pending['password'],
            provider    = 'email',
            role        = 'member',
            status      = 'Pending',
            is_verified = True,
        )
        db.session.add(user)
        db.session.commit()
        session.pop('pending_user', None)

        send_new_user_alert_email(user)
        sync_to_sheets()

        session['user_id'] = user.id
        session['name']    = user.name
        session['role']    = user.role
        session['user']    = user.email
        flash(f'Welcome, {user.name}! Your account is verified.', 'success')
        return redirect(url_for('home'))

    return render_template('verify_otp.html', email=pending.get('email', ''))


@app.route('/resend-otp')
def resend_otp():
    pending = session.get('pending_user')
    if not pending:
        return redirect(url_for('signup'))
    otp = generate_otp()
    pending['otp']     = otp
    pending['expires'] = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    session['pending_user'] = pending
    sent = send_otp_email(pending['email'], pending['name'], otp)
    if not sent:
        print(f'\n[DEV MODE] Resent OTP for {pending["email"]} → {otp}\n')
    flash('New OTP sent to your email.', 'info')
    return redirect(url_for('verify_otp'))


# ─────────────────────────────────────────────────
# AUTH – LOGIN
# ─────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email',    '').strip().lower()
        password = request.form.get('password', '')
        login_type = request.form.get('login_type', 'client')

        if login_type == 'admin':
            if email == ADMIN_EMAIL_LOGIN and password == ADMIN_PASSWORD:
                admin = User.query.filter_by(email=email).first()
                session['user_id'] = admin.id if admin else -1
                session['name']    = 'Admin'
                session['role']    = 'admin'
                session['user']    = email
                flash('Welcome back, Admin!', 'success')
                return redirect(url_for('admin_dashboard'))
            flash('Invalid admin credentials.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()
        if not user or user.provider == 'google':
            flash('No account found. Please sign up.', 'error')
            return render_template('login.html')
        if not check_password_hash(user.password, password):
            flash('Incorrect password.', 'error')
            return render_template('login.html')
        if not user.is_verified:
            flash('Please verify your email first.', 'error')
            return redirect(url_for('verify_otp'))

        session['user_id'] = user.id
        session['name']    = user.name
        session['role']    = user.role
        session['user']    = user.email
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('home'))

    return render_template('login.html')


# ─────────────────────────────────────────────────
# AUTH – GOOGLE OAUTH
# ─────────────────────────────────────────────────
@app.route('/auth/google')
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Google login is not configured. Please use email login.', 'error')
        return redirect(url_for('login'))
    return google_oauth.authorize_redirect(url_for('google_callback', _external=True))


@app.route('/auth/google/callback')
def google_callback():
    try:
        token     = google_oauth.authorize_access_token()
        user_info = token.get('userinfo') or google_oauth.userinfo()
        email     = user_info['email'].lower()
        name      = user_info.get('name', email.split('@')[0])

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email,
                        provider='google', role='member', status='Pending', is_verified=True)
            db.session.add(user)
            db.session.commit()
            send_new_user_alert_email(user)
            sync_to_sheets()
            flash(f'Account created! Welcome, {name}!', 'success')
        else:
            flash(f'Welcome back, {user.name}!', 'success')

        session['user_id'] = user.id
        session['name']    = user.name
        session['role']    = user.role
        session['user']    = user.email
        return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('home'))
    except Exception as e:
        app.logger.error(f'Google OAuth error: {e}')
        flash('Google login failed. Please try again.', 'error')
        return redirect(url_for('login'))


@app.route('/uploads/<path:filename>')
@admin_required
def download_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─────────────────────────────────────────────────
# AUTH – LOGOUT
# ─────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))


# ─────────────────────────────────────────────────
# AUTH – GUEST MODE
# ─────────────────────────────────────────────────
@app.route('/auth/guest')
def guest_mode():
    session.clear()
    session['user_id'] = 'guest'
    session['role']    = 'guest'
    session['name']    = 'Guest'
    flash('Browsing as a Guest. Some features are restricted.', 'info')
    return redirect(url_for('home'))


# ─────────────────────────────────────────────────
# CHATBOT
# ─────────────────────────────────────────────────
@app.route('/chatbot', methods=['POST'])
def chatbot():
    msg = (request.get_json() or {}).get('message', '').lower()
    responses = {
        'hello':      'Hello! Welcome to EduCraft Solutions. How can I help you today?',
        'hi':         "Hi! I'm EduBot. Ask me about overseas education, visas, scholarships, or any service!",
        'overseas':   'We offer complete overseas education support — university selection, SOP, visa, scholarships, and pre-departure guidance. Which country interests you?',
        'visa':       'Our visa experts handle documentation, interview prep, and applications for USA, UK, Canada, Australia, Germany, and more. 98% success rate!',
        'scholarship':'We identify scholarships worth up to 100% tuition waivers. Contact us for a free scholarship report!',
        'university': 'We partner with 500+ universities in 20+ countries. What is your preferred country or field?',
        'research':   'EduCraft offers research consulting, thesis writing, statistical analysis, journal selection, and publication support.',
        'fee':        'First consultation is FREE. Packages start from ₹5,000. Contact us for a detailed quote.',
        'contact':    'Reach us at projecthubpshiksha@gmail.com or +91 9821693299. Office: Subhash Nagar, New Delhi.',
        'ielts':      'We coach IELTS, TOEFL, GRE, GMAT, SAT. Our students average Band 7.5+ in IELTS!',
        'canada':     'Canada offers excellent PR pathways. We handle study permits and university applications.',
        'usa':        'The USA has 4,000+ universities. We help with F1 visa, GRE/GMAT, SOP, and scholarships.',
        'uk':         'UK offers 3-year degrees and a 2-year Graduate Route visa. We support all Student visa applications.',
        'australia':  'Australia offers the 485 Graduate Visa (2–6 years). We have a 98% visa success rate!',
        'germany':    'Public universities in Germany are tuition-free. We guide the entire admission and visa process.',
        'sop':        'Our writers craft compelling SOPs tailored to your profile and target universities. Unlimited revisions included.',
    }
    reply = next((v for k, v in responses.items() if k in msg),
                 'Great question! Book a free consultation or call +91 9821693299 (Mon–Sat 9AM–7PM).')
    return jsonify({'reply': reply})


# ─────────────────────────────────────────────────
# MEMBER / CLIENT DASHBOARDS
# ─────────────────────────────────────────────────
@app.route('/dashboard/member')
@login_required
def member_dashboard():
    if session.get('role') != 'member':
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    return render_template('member_dashboard.html', current_user=user)

@app.route('/request_approval', methods=['POST'])
@login_required
def request_approval():
    user = User.query.get(session['user_id'])
    if user.status == 'Pending':
        user.status = 'Requested'
        db.session.commit()
        # Optionally send an email to ADMIN_EMAIL notifying them of the request
        send_email(ADMIN_EMAIL, f'New Project Access Request: {user.name}', f'<p>{user.name} has requested access.</p>')
        flash('Your request has been submitted to the Admin.', 'success')
    return redirect(url_for('member_dashboard'))

@app.route('/project_access')
@login_required
def project_access():
    user = User.query.get(session['user_id'])
    if user.status != 'Approved' or user.access_used:
        flash('Access denied or already expired.', 'error')
        return redirect(url_for('member_dashboard'))
    
    # Consume access
    user.access_used = True
    user.status = 'Expired'
    db.session.commit()
    flash('One-time access consumed. It has now expired.', 'info')
    return render_template('project_access.html')

@app.route('/dashboard/client')
@login_required
def client_dashboard():
    if session.get('role') != 'client':
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    purchases = Purchase.query.filter_by(user_id=user.id).order_by(Purchase.purchased_at.desc()).all()
    return render_template('client_dashboard.html', current_user=user, purchases=purchases)


@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase_project():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        # Placeholder payment success logic
        new_purchase = Purchase(user_id=user.id, item_name="Premium Service Access", amount=199.99)
        user.role = 'client'
        session['role'] = 'client'
        db.session.add(new_purchase)
        db.session.commit()
        flash('Purchase successful! You have been upgraded to Client.', 'success')
        return redirect(url_for('client_dashboard'))
    return render_template('client_purchase.html')


# ─────────────────────────────────────────────────
# ADMIN – HELPER
# ─────────────────────────────────────────────────
def _gsheet_configured():
    return os.path.exists(GSHEET_KEY_FILE)


# ─────────────────────────────────────────────────
# ADMIN – DASHBOARD
# ─────────────────────────────────────────────────
@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html',
        total_users     = User.query.filter(User.role != 'admin').count(),
        total_messages  = ContactMessage.query.count(),
        unread_msgs     = ContactMessage.query.filter_by(is_read=False).count(),
        total_enquiries = Enquiry.query.count(),
        unread_enq      = Enquiry.query.filter_by(is_read=False).count(),
        recent_msgs     = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).limit(5).all(),
        recent_users    = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).limit(5).all(),
        google_sheet_url  = GOOGLE_SHEET_URL,
        gsheet_configured = _gsheet_configured(),
    )


# ─────────────────────────────────────────────────
# ADMIN – MESSAGES
# ─────────────────────────────────────────────────
@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    ContactMessage.query.update({'is_read': True})
    db.session.commit()
    return render_template('admin/messages.html',
        messages=messages,
        google_sheet_url=GOOGLE_SHEET_URL,
        gsheet_configured=_gsheet_configured(),
    )


@app.route('/admin/messages/delete/<int:mid>', methods=['POST'])
@admin_required
def admin_delete_message(mid):
    db.session.delete(ContactMessage.query.get_or_404(mid))
    db.session.commit()
    sync_to_sheets()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/admin/messages/reply/<int:mid>', methods=['POST'])
@admin_required
def admin_reply_message(mid):
    cm    = ContactMessage.query.get_or_404(mid)
    reply = request.form.get('reply_text', '').strip()
    if not reply:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('admin_messages'))
    reply_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:580px;margin:auto;background:#fff;
                border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
      <div style="background:#1a3c6e;padding:20px 28px">
        <div style="color:#fff;font-size:1rem;font-weight:700">EduCraft Solutions</div>
        <div style="color:rgba(255,255,255,.7);font-size:.76rem">Reply to your enquiry</div>
      </div>
      <div style="padding:24px 28px">
        <p style="color:#1a2332">Hi <strong>{cm.name}</strong>,</p>
        <p style="color:#5a6878;margin-bottom:20px">Thank you for reaching out. Here is our response:</p>
        <div style="background:#f4f7fb;border-left:4px solid #0097a7;padding:16px 20px;
                    border-radius:0 8px 8px 0;color:#1a2332;line-height:1.65">{reply}</div>
        <p style="color:#5a6878;margin-top:20px;font-size:.88rem">
          For further assistance, please call us at <strong>+91 9821693299</strong> (Mon–Sat, 9AM–7PM)
          or reply to this email.
        </p>
      </div>
      <div style="background:#f4f7fb;padding:14px 28px;text-align:center;font-size:.72rem;color:#9aa5b4">
        EduCraft Solutions &nbsp;·&nbsp; 1/191 Subhash Nagar, New Delhi – 110027
        &nbsp;·&nbsp; projecthubpshiksha@gmail.com
      </div>
    </div>"""
    if send_email(cm.email, 'Re: Your Enquiry – EduCraft Solutions', reply_body):
        flash(f'Reply sent to {cm.email}.', 'success')
    else:
        flash('Failed to send email. Check SMTP settings in .env', 'error')
    return redirect(url_for('admin_messages'))


# ─────────────────────────────────────────────────
# ADMIN – ENQUIRIES
# ─────────────────────────────────────────────────
@app.route('/admin/enquiries')
@admin_required
def admin_enquiries():
    enquiries = Enquiry.query.order_by(Enquiry.submitted_at.desc()).all()
    Enquiry.query.update({'is_read': True})
    db.session.commit()
    return render_template('admin/enquiries.html',
        enquiries=enquiries,
        google_sheet_url=GOOGLE_SHEET_URL,
        gsheet_configured=_gsheet_configured(),
    )


@app.route('/admin/enquiries/delete/<int:eid>', methods=['POST'])
@admin_required
def admin_delete_enquiry(eid):
    db.session.delete(Enquiry.query.get_or_404(eid))
    db.session.commit()
    sync_to_sheets()
    flash('Enquiry deleted.', 'success')
    return redirect(url_for('admin_enquiries'))


@app.route('/admin/enquiries/reply/<int:eid>', methods=['POST'])
@admin_required
def admin_reply_enquiry(eid):
    enq   = Enquiry.query.get_or_404(eid)
    reply = request.form.get('reply_text', '').strip()
    if not reply:
        flash('Reply cannot be empty.', 'error')
        return redirect(url_for('admin_enquiries'))
    country_line = f'in {enq.country}' if enq.country else 'abroad'
    details_line = ''
    if enq.country or enq.course:
        parts = []
        if enq.country: parts.append(f'Country: {enq.country}')
        if enq.course:  parts.append(f'Course: {enq.course}')
        if enq.budget:  parts.append(f'Budget: {enq.budget}')
        details_line = f"""
        <p style="color:#5a6878;margin-top:16px;font-size:.86rem">
          <strong>Your Enquiry Details:</strong><br>{'  &nbsp;|&nbsp;  '.join(parts)}
        </p>"""
    reply_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:580px;margin:auto;background:#fff;
                border:1px solid #e2e8f0;border-radius:14px;overflow:hidden">
      <div style="background:#0097a7;padding:20px 28px">
        <div style="color:#fff;font-size:1rem;font-weight:700">EduCraft Solutions</div>
        <div style="color:rgba(255,255,255,.75);font-size:.76rem">Reply to your Study Abroad Enquiry</div>
      </div>
      <div style="padding:24px 28px">
        <p style="color:#1a2332">Hi <strong>{enq.name}</strong>,</p>
        <p style="color:#5a6878;margin-bottom:20px">
          Thank you for your interest in studying {country_line}.
          Here is our response to your enquiry:
        </p>
        <div style="background:#f4f7fb;border-left:4px solid #0097a7;padding:16px 20px;
                    border-radius:0 8px 8px 0;color:#1a2332;line-height:1.65">{reply}</div>
        {details_line}
        <p style="color:#5a6878;margin-top:20px;font-size:.88rem">
          For further assistance, call us at <strong>+91 9821693299</strong> (Mon–Sat, 9AM–7PM)
          or reply to this email.
        </p>
      </div>
      <div style="background:#f4f7fb;padding:14px 28px;text-align:center;font-size:.72rem;color:#9aa5b4">
        EduCraft Solutions &nbsp;·&nbsp; 1/191 Subhash Nagar, New Delhi – 110027
        &nbsp;·&nbsp; projecthubpshiksha@gmail.com
      </div>
    </div>"""
    if send_email(enq.email, 'Re: Your Study Abroad Enquiry – EduCraft Solutions', reply_body):
        flash(f'Reply sent to {enq.email}.', 'success')
    else:
        flash('Failed to send email. Check SMTP settings in .env', 'error')
    return redirect(url_for('admin_enquiries'))


# ─────────────────────────────────────────────────
# ADMIN – USERS
# ─────────────────────────────────────────────────
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html',
        users=users,
        google_sheet_url=GOOGLE_SHEET_URL,
        gsheet_configured=_gsheet_configured(),
    )


@app.route('/admin/users/status/<int:uid>', methods=['POST'])
@admin_required
def admin_update_user_status(uid):
    user = User.query.get_or_404(uid)
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Requested', 'Approved', 'Rejected', 'Expired']:
        user.status = new_status
        if new_status == 'Approved':
            user.access_used = False
        db.session.commit()
        sync_to_sheets()
        flash(f'Status for {user.name} updated to {new_status}.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/delete/<int:uid>', methods=['POST'])
@admin_required
def admin_delete_user(uid):
    user = User.query.get_or_404(uid)
    if user.role == 'admin':
        flash('Cannot delete admin user.', 'error')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    sync_to_sheets()
    flash(f'User {user.email} deleted.', 'success')
    return redirect(url_for('admin_users'))


# ─────────────────────────────────────────────────
# PROJECT MANAGEMENT SYSTEM (PMS)
# ─────────────────────────────────────────────────
@app.route('/pms/dashboard')
@login_required
def pms_dashboard():
    role = session.get('role')
    user = User.query.get(session['user_id'])
    if role == "admin":
        projects = Project.query.all()
    elif role == "client":
        projects = Project.query.filter_by(client_email=user.email).all()
    else:
        flash("You are not authorized to view the Project Dashboard.", "error")
        return redirect(url_for('home'))

    return render_template("pms/dashboard.html",
                           projects=projects,
                           total=len(projects),
                           in_progress=len([p for p in projects if p.status == "In Progress"]),
                           completed=len([p for p in projects if p.status == "Completed"]),
                           on_hold=len([p for p in projects if p.status == "On Hold"]),
                           pending=len([p for p in projects if p.status == "Pending"]),
                           current_user=user)

@app.route('/pms/complete_milestone/<int:project_id>/<int:m_index>', methods=['POST'])
@admin_required
def pms_complete_milestone(project_id, m_index):
    project = Project.query.get_or_404(project_id)
    milestones = json.loads(project.milestones) if project.milestones else []

    if 0 <= m_index < len(milestones):
        milestones[m_index]["done"] = True

    total = len(milestones)
    completed = len([m for m in milestones if m["done"]])
    new_progress = int((completed / total) * 100) if total > 0 else 0

    project.progress = new_progress
    project.milestones = json.dumps(milestones)

    if new_progress == 100:
        project.status = "Completed"
    elif new_progress > 0:
        project.status = "In Progress"

    db.session.commit()

    subject = f"Milestone Completed - {project.name}"
    body = f"""
    Hello {project.client_name},
    
    A milestone has been completed.
    Current Progress: {project.progress}%
    Project Status: {project.status}
    
    Regards,
    EduCraft Solutions Team
    """
    send_email(project.client_email, subject, body)

    flash("Milestone completed and progress updated!", "success")
    return redirect(url_for('pms_project_detail', id=project.id))

@app.route('/pms/add_project', methods=['GET', 'POST'])
@admin_required
def pms_add_project():
    clients = User.query.filter_by(role='client').all()

    if request.method == 'POST':
        client_id = request.form.get('client_id')
        client = User.query.get(client_id)
        if not client:
            flash("Please select a valid client.", "error")
            return redirect(url_for('pms_add_project'))

        milestone_names = request.form.get('milestones', '').split(',')
        milestones_data = [
            {"name": m.strip(), "done": False}
            for m in milestone_names if m.strip()
        ]

        if not milestones_data:
            flash("Please enter at least one milestone.", "error")
            return redirect(url_for('pms_add_project'))

        initial_progress = int(request.form.get('progress', 0))

        new_project = Project(
            name=request.form.get('name'),
            description=request.form.get('description'),
            client_name=client.name,
            client_email=client.email,
            client_phone=request.form.get('client_phone') or client.phone,
            status=request.form.get('status'),
            progress=initial_progress,
            start_date=request.form.get('start_date'),
            deadline=request.form.get('deadline'),
            tech_stack=request.form.get('tech_stack'),
            milestones=json.dumps(milestones_data)
        )

        db.session.add(new_project)
        db.session.commit()

        flash("Project added successfully!", "success")
        return redirect(url_for('pms_dashboard'))

    return render_template('pms/add_project.html', clients=clients)

@app.route('/pms/project/<int:id>')
@login_required
def pms_project_detail(id):
    project = Project.query.get_or_404(id)
    role = session.get('role')
    user = User.query.get(session['user_id'])

    if role == "client" and project.client_email != user.email:
        flash("You are not authorized to view this project.", "error")
        return redirect(url_for('pms_dashboard'))

    milestones = json.loads(project.milestones) if project.milestones else []
    return render_template('pms/project_detail.html', project=project, milestones=milestones, current_user=user)

@app.route('/pms/delete/<int:id>', methods=['POST'])
@admin_required
def pms_delete_project(id):
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully.", "success")
    return redirect(url_for('pms_dashboard'))


# ─────────────────────────────────────────────────
# ADMIN – MANUAL SYNC TO SHEETS
# ─────────────────────────────────────────────────
@app.route('/admin/sync-sheets', methods=['POST'])
@admin_required
def admin_sync_sheets():
    if not _gsheet_configured():
        flash('Google Sheets not configured. See GOOGLE_SHEETS_SETUP.md for instructions.', 'error')
    else:
        try:
            sync_to_sheets()
            flash('✅ Google Sheets synced successfully!', 'success')
        except Exception as e:
            flash(f'Sync failed: {e}', 'error')
    return redirect(request.referrer or url_for('admin_dashboard'))


# ─────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


# ─────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)