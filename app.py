import os
import zipfile
import cloudconvert
from flask import Flask, render_template, request, send_file
from io import BytesIO
from PIL import Image
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configurar a API Key do CloudConvert (vai ser definida como variável no Render)
API_KEY = os.environ.get('CLOUDCONVERT_API_KEY')
cloudconvert.configure(api_key=API_KEY)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            return 'Nenhum arquivo selecionado'

        filename = os.path.splitext(pdf_file.filename)[0]
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        pdf_file.save(pdf_path)

        # Criar Job no CloudConvert
        job = cloudconvert.Job.create(payload={
            "tasks": {
                "import-my-file": {
                    "operation": "import/upload"
                },
                "convert-my-file": {
                    "operation": "convert",
                    "input": "import-my-file",
                    "input_format": "pdf",
                    "output_format": "png",
                    "engine": "poppler",
                    "output_format_options": {
                        "density": 300
                    }
                },
                "export-my-file": {
                    "operation": "export/url",
                    "input": "convert-my-file"
                }
            }
        })

        # Enviar PDF para o CloudConvert
        upload_task = job['tasks'][0]
        upload_url = upload_task['result']['form']['url']
        upload_params = upload_task['result']['form']['parameters']

        with open(pdf_path, 'rb') as file_data:
            files = {'file': file_data}
            requests.post(upload_url, data=upload_params, files=files)

        # Aguardar fim da conversão
        job = cloudconvert.Job.wait(id=job['id'])
        export_task = [task for task in job['tasks'] if task['name'] == 'export-my-file'][0]
        file_url = export_task['result']['files'][0]['url']

        # Download do PNG
        response = requests.get(file_url)
        png_image_bytes = response.content

        # Criar pasta ZIP com PNG + JPG
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Nome do PNG
            png_name = f"{filename}.png"
            zip_file.writestr(f"{filename}/{png_name}", png_image_bytes)

            # Gerar JPG (90px height)
            image = Image.open(BytesIO(png_image_bytes)).convert("RGB")
            width, height = image.size
            new_width = int((90 / height) * width)
            jpg_image = image.resize((new_width, 90))
            jpg_buffer = BytesIO()
            jpg_image.save(jpg_buffer, format="JPEG")
            zip_file.writestr(f"{filename}/{filename}.jpg", jpg_buffer.getvalue())

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{filename}.zip"
        )

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
