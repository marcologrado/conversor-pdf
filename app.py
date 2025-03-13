import os
import cloudconvert
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# API KEY DIRETA
API_KEY = "sk_live_0e0C***************"

# Instanciar cliente correto
cloudconvert_api = cloudconvert.Client(api_key=API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return 'No file part'
        file = request.files['pdf_file']
        if file.filename == '':
            return 'No selected file'

        # Criar o Job no CloudConvert
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
                    "page_range": "1",
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

        # Obter o link de upload
        upload_task = job['tasks'][0]
        upload_url = upload_task['result']['form']['url']

        # Upload do ficheiro
        with file.stream as file_stream:
            cloudconvert_api.tasks.upload(upload_task, file_stream)

        return 'Conversão iniciada com sucesso! Verifica o painel do CloudConvert.'

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
