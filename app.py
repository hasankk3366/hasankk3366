from flask import Flask, render_template, request

app = Flask(__name__)

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
        mesaj = request.form.get("mesaj")
        print(f"Yeni mesaj: {isim} - {mesaj}")
        return render_template("iletisim.html", aktif_sayfa="iletisim", basarili=True)
    return render_template("iletisim.html", aktif_sayfa="iletisim")

if __name__ == "__main__":
    app.run(debug=True)
