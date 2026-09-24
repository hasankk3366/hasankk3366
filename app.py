import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "gizli-anahtar-degistir")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── Telegram ──
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


# ── Modeller ──
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kullanici_adi = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    sifre_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    kayit_tarihi = db.Column(db.DateTime, default=datetime.now)


class Mesaj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    mesaj = db.Column(db.Text, nullable=False)
    tarih = db.Column(db.DateTime, default=datetime.now)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Telegram bildirim ──
def telegram_bildirim_gonder(isim, mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram ayarları eksik!")
        return
    metin = f"📬 Yeni Mesaj!\n\n👤 {isim}\n💬 {mesaj}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": metin}, timeout=5)
    except Exception as e:
        print(f"Telegram hatası: {e}")


# ── Sayfalar ──
@app.route("/")
def index():
    return render_template("index.html", aktif_sayfa="index")


@app.route("/hakkimda")
def hakkimda():
    return render_template("hakkimda.html", aktif_sayfa="hakkimda")


@app.route("/iletisim", methods=["GET", "POST"])
def iletisim():
    if request.method == "POST":
        isim = request.form.get("isim")
        email = request.form.get("email")
        mesaj_metni = request.form.get("mesaj")
        yeni = Mesaj(isim=isim, email=email, mesaj=mesaj_metni)
        db.session.add(yeni)
        db.session.commit()
        telegram_bildirim_gonder(isim, mesaj_metni)
        flash("Mesajın başarıyla gönderildi! 🎉", "basari")
        return redirect(url_for("iletisim"))
    return render_template("iletisim.html", aktif_sayfa="iletisim")


@app.route("/kayit", methods=["GET", "POST"])
def kayit():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        kullanici_adi = request.form.get("kullanici_adi")
        email = request.form.get("email")
        sifre = request.form.get("sifre")

        if User.query.filter_by(kullanici_adi=kullanici_adi).first():
            flash("Bu kullanıcı adı zaten alınmış.", "hata")
            return redirect(url_for("kayit"))
        if User.query.filter_by(email=email).first():
            flash("Bu e-posta zaten kayıtlı.", "hata")
            return redirect(url_for("kayit"))

        # İlk kullanıcı otomatik admin olur
        ilk_kullanici = User.query.count() == 0
        yeni = User(
            kullanici_adi=kullanici_adi,
            email=email,
            sifre_hash=generate_password_hash(sifre),
            is_admin=ilk_kullanici
        )
        db.session.add(yeni)
        db.session.commit()
        flash("Kayıt başarılı! Şimdi giriş yapabilirsin.", "basari")
        return redirect(url_for("login"))
    return render_template("kayit.html", aktif_sayfa="kayit")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        kullanici_adi = request.form.get("kullanici_adi")
        sifre = request.form.get("sifre")
        user = User.query.filter_by(kullanici_adi=kullanici_adi).first()
        if user and check_password_hash(user.sifre_hash, sifre):
            login_user(user)
            flash(f"Hoş geldin, {user.kullanici_adi}! 👋", "basari")
            return redirect(url_for("index"))
        flash("Kullanıcı adı veya şifre yanlış.", "hata")
    return render_template("login.html", aktif_sayfa="login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Çıkış yapıldı.", "basari")
    return redirect(url_for("index"))


@app.route("/admin/mesajlar")
@login_required
def admin_mesajlar():
    if not current_user.is_admin:
        flash("Bu sayfaya erişim yetkin yok.", "hata")
        return redirect(url_for("index"))
    tum_mesajlar = Mesaj.query.order_by(Mesaj.tarih.desc()).all()
    return render_template("admin_mesajlar.html", mesajlar=tum_mesajlar)


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)