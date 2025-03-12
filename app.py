from flask import Flask, request, render_template, send_file
from pdf2image import convert_from_path
import os
from PIL import Image
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        pdf = request.files["file"]
        filename = os.path.splitext(pdf.filename)[0]  # Nome do arquivo sem extensão
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf.filename)
        pdf.save(pdf_path)

        # Criar pasta com o nome do arquivo
        output_folder = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Converter PDF para imagem
        images = convert_from_path(pdf_path)

        # Salvar PNG dentro da pasta
        png_path = os.path.join(output_folder, f"{filename}.png")
        images[0].save(png_path, "PNG")

        # Redimensionar PNG para altura máxima de 3070px
        img = Image.open(png_path)
        width, height = img.size
        if height > 3070:
            new_width = int((3070 / height) * width)
            img = img.resize((new_width, 3070), Image.LANCZOS)
            img.save(png_path, "PNG")

        # Salvar JPG dentro da pasta com altura de 90px
        jpg_path = os.path.join(output_folder, f"{filename}.jpg")
        img_jpg = img.resize((int((90 / img.height) * img.width), 90), Image.LANCZOS)
        img_jpg.save(jpg_path, "JPEG", quality=90)

        # Retornar um ZIP contendo os arquivos
        zip_path = os.path.join(UPLOAD_FOLDER, f"{filename}.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(png_path, os.path.basename(png_path))
            zipf.write(jpg_path, os.path.basename(jpg_path))

        return send_file(zip_path, as_attachment=True)

    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Porta dinâmica para Railway
    app.run(debug=False, host="0.0.0.0", port=port)
