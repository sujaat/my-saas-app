from flask import Flask, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.mime.text import MIMEText
import random, string

app = Flask(__name__)
app.secret_key = "easy_saas"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.db"
db = SQLAlchemy(app)

# ---------------- USERS ----------------
users = {"admin": "admin"}

# ---------------- SMART LINKS ----------------
class SmartLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True)
    mobile = db.Column(db.String(300))
    desktop = db.Column(db.String(300))

db.create_all()

# ---------------- SMTP (PUT YOUR DETAILS) ----------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL = "your_email@gmail.com"
PASSWORD = "your_app_password"

def send_email(to, subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to

    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, to, msg.as_string())
    server.quit()

# ---------------- DEVICE CHECK ----------------
def is_mobile(user_agent):
    ua = user_agent.lower()
    return "android" in ua or "iphone" in ua

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in users and users[u] == p:
            session["user"] = u
            return redirect("/dashboard")

        return "Wrong Login"

    return """
    <h2>Login</h2>
    <form method="post">
    <input name="username" placeholder="user"><br>
    <input name="password" type="password" placeholder="pass"><br>
    <button>Login</button>
    </form>
    """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return """
    <h2>Dashboard</h2>
    <a href="/send">Send Email</a><br>
    <a href="/create-link">Create Smart Link</a><br>
    <a href="/logout">Logout</a>
    """

# ---------------- EMAIL ----------------
@app.route("/send", methods=["GET","POST"])
def send():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        to = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        send_email(to, subject, message)
        return "Email Sent"

    return """
    <h2>Send Email</h2>
    <form method="post">
    <input name="email" placeholder="to"><br>
    <input name="subject" placeholder="subject"><br>
    <textarea name="message"></textarea><br>
    <button>Send</button>
    </form>
    """

# ---------------- CREATE SMART LINK ----------------
@app.route("/create-link", methods=["GET","POST"])
def create_link():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        link = SmartLink(
            code=code,
            mobile=request.form["mobile"],
            desktop=request.form["desktop"]
        )

        db.session.add(link)
        db.session.commit()

        return f"Your link: /r/{code}"

    return """
    <h2>Create Smart Link</h2>
    <form method="post">
    Mobile URL:<br>
    <input name="mobile"><br>
    Desktop URL:<br>
    <input name="desktop"><br>
    <button>Create</button>
    </form>
    """

# ---------------- SMART REDIRECT ----------------
@app.route("/r/<code>")
def redirect_link(code):
    link = SmartLink.query.filter_by(code=code).first()

    if not link:
        return "Invalid Link"

    if is_mobile(request.headers.get("User-Agent")):
        return redirect(link.mobile)
    else:
        return redirect(link.desktop)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run()
