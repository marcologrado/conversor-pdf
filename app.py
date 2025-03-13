import os
import cloudconvert
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# API Key diretamente no código (como pediste!)
API_KEY = "sk_live_0e0C***************"  # <-- tua key real aqui

# Inicializar API
cloudconvert_api = cloudconvert.Api(API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return 'No file part'
        file = request.files['pdf_file']
        if file.filename == '':
            return 'No selected file'
        
        # Criação do job CloudConvert
        job = cloudconvert_api.jobs.create(payload={
            "tasks": {
                'import-my-file': {
                    'operation': 'import/upload'
                },
                'convert-my-file': {
                    'operation': 'convert',
                    'input': 'import-my-file',
                    'input_format': 'pdf',
                    'output_format': 'png',
                    "page_range": "1",  # Apenas a primeira página (ajustável)
                    "engine": "poppler"
                },
                'export-my-file': {
                    'operation': 'export/url',
                    'input': 'convert-my-file',
                    'inline': False,
                    'archive_multiple_files': False
                }
            }
        })

        # Obter o URL de upload
        upload_task = job['tasks'][0]
        upload_url = upload_task['result']['form']['url']

        # Fazer upload do ficheiro para CloudConvert
        with file.stream as file_stream:
            cloudconvert_api.tasks.upload(upload_task, file_stream)

        return 'Conversão iniciada com sucesso! Verifica o CloudConvert Jobs.'

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
