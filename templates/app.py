from flask import Flask, request, render_template, send_file
from pdf2image import convert_from_path
import os

app = Flask(__name__)

# Pasta temporária para armazenar os arquivos
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        pdf = request.files["file"]
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(pdf_path)

        # Converter PDF para imagem
        images = convert_from_path(pdf_path)
        img_path = os.path.join(UPLOAD_FOLDER, "output.png")
        images[0].save(img_path, "PNG")

        return send_file(img_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
