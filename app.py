import os
from flask import Flask, render_template, request, send_file
import cloudconvert
from dotenv import load_dotenv
import requests
import time

# 🔑 Chave da API (substituída aqui como pediste)
API_KEY = "q6xLk8tKcCzq7Q3rTfP9wG4vWbBVZ7Fh4gTlfqfvlNY0NDbJ6eFyOSzIRjfpT9P1"

# Inicializar o cliente CloudConvert
api = cloudconvert.Client(api_key=API_KEY)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return 'No file part'

    file = request.files['pdf_file']

    if file.filename == '':
        return 'No selected file'

    if file:
        filename = file.filename
        basename = os.path.splitext(filename)[0]  # "001.pdf" -> "001"

        # Guardar o ficheiro temporariamente
        input_path = f"uploads/{filename}"
        output_folder = f"uploads/{basename}"
        os.makedirs(output_folder, exist_ok=True)
        file.save(input_path)

        # Criar o job na CloudConvert
        job = api.jobs.create(payload={
            "tasks": {
                'import-1': {
                    'operation': 'import/upload'
                },
                'convert-1-png': {
                    'operation': 'convert',
                    'input': 'import-1',
                    'output_format': 'png'
                },
                'convert-2-jpg': {
                    'operation': 'convert',
                    'input': 'import-1',
                    'output_format': 'jpg'
                },
                'export-1': {
                    'operation': 'export/url',
                    'input': ['convert-1-png', 'convert-2-jpg'],
                    'inline': False,
                    'archive_multiple_files': True
                }
            }
        })

        # Obter URL de upload
        upload_task = job['tasks'][0]  # import-1
        upload_url = upload_task['result']['form']['url']
        upload_parameters = upload_task['result']['form']['parameters']

        # Fazer o upload do ficheiro para o URL indicado
        with open(input_path, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(upload_url, data=upload_parameters, files=files)
            response.raise_for_status()

        # Aguardar a conclusão
        job_id = job['id']
        while True:
            job_status = api.jobs.get(job_id)
            if job_status['status'] == 'finished':
                break
            elif job_status['status'] == 'error':
                return 'Erro no processamento do ficheiro.'
            time.sleep(3)  # Espera 3 segundos antes de verificar novamente

        # Obter o link do ficheiro zip final
        export_task = next(task for task in job_status['tasks'] if task['name'] == 'export-1')
        file_url = export_task['result']['files'][0]['url']

        # Fazer o download do ficheiro zip
        output_zip_path = os.path.join(output_folder, f"{basename}.zip")
        r = requests.get(file_url)
        with open(output_zip_path, 'wb') as f:
            f.write(r.content)

        # Retornar o ZIP ao utilizador
        return send_file(output_zip_path, as_attachment=True, download_name=f"{basename}.zip")

if __name__ == '__main__':
    app.run(debug=True)
