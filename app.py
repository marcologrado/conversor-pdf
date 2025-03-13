from flask import Flask, render_template, request, send_file
import os
import cloudconvert
import requests  # Não esquecer de ter o requests no requirements.txt

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ AQUI ESTÁ A API KEY DIRETA:
API_KEY = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI2NmYxZDU0Yy1jZjc4LTQ1MzMtYjE1My1hYzRkZTRlMTRjOTciLCJqdGkiOiI2NzFiZGE0Mi03ZThmLTRhNWItOGI4ZS02NzBiZjhkYjVhZWQiLCJpc3MiOiJjbG91ZGNvbnZlcnQuYXBpIiwiaWF0IjoxNzA5NjM0NjE2fQ.TQj04TwBMG8Kcr3YltpMHydqvm8yqPU9hSn8ZW_Mt2E'
cloudconvert.configure(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # ✅ Criação do job na CloudConvert
    job = cloudconvert.Job.create(payload={
        "tasks": {
            'import-my-file': {
                'operation': 'import/upload'
            },
            'convert-my-file': {
                'operation': 'convert',
                'input': 'import-my-file',
                'input_format': 'pdf',
                'output_format': 'jpg',
                'engine': 'office',  # ou 'imagem' se quiser testar outro
                'engine_version': '1.0'
            },
            'export-my-file': {
                'operation': 'export/url',
                'input': 'convert-my-file'
            }
        }
    })

    # ✅ Pega ID da tarefa de upload
    import_task_id = job['tasks'][0]['id']
    upload_task = cloudconvert.Task.find(id=import_task_id)

    # ✅ URL para upload
    upload_url = upload_task['result']['form']['url']
    upload_parameters = upload_task['result']['form']['parameters']

    # ✅ Upload do PDF
    with open(file_path, 'rb') as file_data:
        response = requests.post(upload_url, data=upload_parameters, files={'file': file_data})
        print('Upload Response:', response.status_code, response.text)

    return 'File uploaded and conversion started! Check your CloudConvert dashboard.'

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
