from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from email.mime.text import MIMEText
import json
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ================= DATABASE MODELS =================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))


class Project(db.Model):
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= EMAIL CONFIG =================

EMAIL_ADDRESS = "projecthubpshiksha@gmail.com"
EMAIL_PASSWORD = "otlehwxxdwkolpba"

def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()

        print("✅ Email sent successfully!")

    except Exception as e:
        print("❌ Email failed:", e)

# ================= OTP FUNCTION =================

def send_otp_email(receiver_email, otp):
    subject = "Your ProjectHub Login OTP"
    body = f"""
Hello,

Your OTP for login is: {otp}

This OTP will expire in 5 minutes.

Regards,
ProjectHub Team
"""
    send_email(receiver_email, subject, body)

# ================= ROUTES =================

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

# ---------- REGISTER ----------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'])

        new_user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=hashed_password,
            role=request.form['role']
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!")
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------- LOGIN ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):

            # 🔥 ADMIN → DIRECT LOGIN (NO OTP)
            if user.role == "admin":
                login_user(user)
                return redirect(url_for('dashboard'))

            # 🔥 CLIENT → OTP LOGIN
            else:
                otp = str(random.randint(100000, 999999))
                session['otp'] = otp
                session['otp_expiry'] = time.time() + 300
                session['temp_user_id'] = user.id

                send_otp_email(user.email, otp)

                return redirect(url_for('verify_otp'))

        flash("Invalid credentials")

    return render_template('login.html')

# ---------- VERIFY OTP (CLIENT ONLY) ----------

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':

        # Expiry check
        if time.time() > session.get('otp_expiry', 0):
            flash("OTP expired. Please login again.")
            return redirect(url_for('login'))

        entered_otp = request.form['otp']

        if entered_otp == session.get('otp'):
            user = User.query.get(session.get('temp_user_id'))
            login_user(user)

            session.pop('otp', None)
            session.pop('otp_expiry', None)
            session.pop('temp_user_id', None)

            return redirect(url_for('dashboard'))

        flash("Invalid OTP")

    return render_template('verify_otp.html')

# ---------- DASHBOARD ----------

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == "admin":
        projects = Project.query.all()
    else:
        projects = Project.query.filter_by(client_name=current_user.username).all()

    return render_template("dashboard.html",
                           projects=projects,
                           total=len(projects),
                           in_progress=len([p for p in projects if p.status == "In Progress"]),
                           completed=len([p for p in projects if p.status == "Completed"]),
                           on_hold=len([p for p in projects if p.status == "On Hold"]),
                           pending=len([p for p in projects if p.status == "Pending"]))

# ---------- COMPLETE MILESTONE ----------

@app.route('/complete_milestone/<int:project_id>/<int:m_index>', methods=['POST'])
@login_required
def complete_milestone(project_id, m_index):

    if current_user.role != "admin":
        return "Unauthorized", 403

    project = Project.query.get_or_404(project_id)
    milestones = json.loads(project.milestones)

    if 0 <= m_index < len(milestones):
        milestones[m_index]["done"] = True

    total = len(milestones)
    completed = len([m for m in milestones if m["done"]])

    # 🔥 Override manual progress with milestone progress
    new_progress = int((completed / total) * 100)

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
ProjectHub Team
"""

    send_email(project.client_email, subject, body)

    flash("Milestone completed and progress updated!")
    return redirect(url_for('project_detail', id=project.id))

# ---------- ADD PROJECT ----------

@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():

    if current_user.role != "admin":
        return "Unauthorized", 403

    clients = User.query.filter_by(role='client').all()

    if request.method == 'POST':

        client_id = request.form.get('client_id')
        client = User.query.get(client_id)

        if not client:
            flash("Please select a valid client.")
            return redirect(url_for('add_project'))

        milestone_names = request.form.get('milestones', '').split(',')

        milestones_data = [
            {"name": m.strip(), "done": False}
            for m in milestone_names if m.strip()
        ]

        if not milestones_data:
            flash("Please enter at least one milestone.")
            return redirect(url_for('add_project'))

        initial_progress = int(request.form.get('progress', 0))

        project = Project(
            name=request.form.get('name'),
            description=request.form.get('description'),
            client_name=client.username,
            client_email=client.email,
            client_phone=request.form.get('client_phone'),
            status=request.form.get('status'),
            progress=initial_progress,  # 🔥 Manual initial progress
            start_date=request.form.get('start_date'),
            deadline=request.form.get('deadline'),
            tech_stack=request.form.get('tech_stack'),
            milestones=json.dumps(milestones_data)
        )

        db.session.add(project)
        db.session.commit()

        flash("Project added successfully!")
        return redirect(url_for('dashboard'))

    return render_template('add_project.html', clients=clients)

# ---------- PROJECT DETAIL ----------

@app.route('/project/<int:id>')
@login_required
def project_detail(id):
    project = Project.query.get_or_404(id)

    # Client can only see their own project
    if current_user.role == "client" and project.client_name != current_user.username:
        flash("You are not authorized to view this project.")
        return redirect(url_for('dashboard'))

    milestones = json.loads(project.milestones)

    return render_template(
        'project_detail.html',
        project=project,
        milestones=milestones
    )

# ---------- DELETE PROJECT ----------

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_project(id):

    if current_user.role != "admin":
        return "Unauthorized", 403

    project = Project.query.get_or_404(id)

    db.session.delete(project)
    db.session.commit()

    flash("Project deleted successfully.")
    return redirect(url_for('dashboard'))

# ---------------- CHATBOT ----------------

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():

    try:
        data = request.get_json()
        message = data.get("message", "").lower().strip()

        # Get admin email
        admin = User.query.filter_by(role="admin").first()
        admin_email = admin.email if admin else "admin@projecthub.com"

        # Greeting
        if any(word in message for word in ["hi", "hello", "hey"]):
            return jsonify({"reply": f"Hi {current_user.username}! 👋 How can I help you today?"})

        # Bye
        if any(word in message for word in ["bye", "goodbye", "see you"]):
            return jsonify({"reply": "Goodbye 👋 Have a great day!"})

        # Thanks
        if any(word in message for word in ["thank", "thanks"]):
            return jsonify({"reply": "You're welcome 😊 Always happy to help!"})

        # Get projects based on role
        if current_user.role == "admin":
            projects = Project.query.all()
        else:
            projects = Project.query.filter_by(client_name=current_user.username).all()

        if not projects:
            return jsonify({"reply": "You currently have no projects assigned."})

        # Total projects
        if "total" in message or "how many" in message:
            return jsonify({"reply": f"You have {len(projects)} project(s)."})

        # List projects
        if "list" in message or "my projects" in message:
            names = ", ".join([p.name for p in projects])
            return jsonify({"reply": f"Your projects are: {names}"})

        # Loop through projects
        for p in projects:

            if p.name.lower() in message:

                if "deadline" in message:
                    return jsonify({"reply": f"Deadline for {p.name} is {p.deadline}."})

                if "progress" in message:
                    return jsonify({"reply": f"{p.name} is {p.progress}% completed."})

                if "status" in message:
                    return jsonify({"reply": f"Current status of {p.name} is {p.status}."})

                if "tech" in message:
                    return jsonify({"reply": f"{p.name} uses {p.tech_stack}."})

                if "milestone" in message:
                    milestones = json.loads(p.milestones)
                    completed = [m["name"] for m in milestones if m["done"]]
                    pending = [m["name"] for m in milestones if not m["done"]]

                    return jsonify({
                        "reply": f"Completed: {', '.join(completed) if completed else 'None'} | Pending: {', '.join(pending) if pending else 'None'}"
                    })

                # General project info
                return jsonify({
                    "reply": f"{p.name} is {p.progress}% completed and currently {p.status}."
                })

        # Unknown question
        return jsonify({
            "reply": f"I’m not sure about that 🤔 Please contact the admin at {admin_email}."
        })

    except Exception as e:
        print("Chatbot Error:", e)
        return jsonify({"reply": "Something went wrong. Please try again."})

# ---------- LOGOUT ----------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ================= INIT DB =================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)
