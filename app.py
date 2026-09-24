import os
import requests
from datetime import datetime
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ── Veritabanı Ayarları ──
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mesajlar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ── Telegram Ayarları ──
# Render'da Environment Variables olarak ekleyeceğiz.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


# ── Veritabanı Modeli ──
class Mesaj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False)
    mesaj = db.Column(db.Text, nullable=False)
    tarih = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Mesaj {self.isim}>"


# ── Telegram Bildirim Fonksiyonu ──
def telegram_bildirim_gonder(isim, mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram ayarları eksik!")
        return
    metin = f"📬 Yeni Mesaj!\n\n👤 {isim}\n💬 {mesaj}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": metin}, timeout=5)
        if r.status_code != 200:
            print(f"Telegram hatası: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Telegram bağlantı hatası: {e}")


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
        mesaj_metni = request.form.get("mesaj")

        # 1) Veritabanına kaydet
        yeni_mesaj = Mesaj(isim=isim, mesaj=mesaj_metni)
        db.session.add(yeni_mesaj)
        db.session.commit()

        # 2) Telegram'a bildirim gönder
        telegram_bildirim_gonder(isim, mesaj_metni)

        # 3) Kullanıcıya başarılı mesajı göster
        return render_template("iletisim.html", aktif_sayfa="iletisim", basarili=True)

    return render_template("iletisim.html", aktif_sayfa="iletisim")


# ── Admin Sayfası (mesajları oku) ──
@app.route("/admin/mesajlar")
def admin_mesajlar():
    tum_mesajlar = Mesaj.query.order_by(Mesaj.tarih.desc()).all()
    return render_template("admin_mesajlar.html", mesajlar=tum_mesajlar)


# ── Uygulama Başlat ──
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)