from flask import Flask, render_template, request, send_file
import os
import cloudconvert
from dotenv import load_dotenv
import requests
import time

load_dotenv()

app = Flask(__name__)

# API Key correta
API_KEY = "aJq3n2wVZ0hRzB0vFJk9fjVnL0N0z5aM4PZ5Yg3H0gC7i4X0R2E6M2F7g0k2d4X0"

cloudconvert_api = cloudconvert.Client(API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return "No file part", 400
        file = request.files['pdf_file']
        if file.filename == '':
            return "No selected file", 400
        if file:
            filename = file.filename
            filepath = os.path.join('/tmp', filename)
            file.save(filepath)

            print(f"📥 PDF recebido: {filename}")

            try:
                print("🚀 A criar job na CloudConvert...")
                job = cloudconvert_api.jobs.create(payload={
                    "tasks": {
                        'import-my-file': {
                            'operation': 'import/upload'
                        },
                        'convert-my-file': {
                            'operation': 'convert',
                            'input': 'import-my-file',
                            'output_format': 'jpg'
                        },
                        'export-my-file': {
                            'operation': 'export/url',
                            'input': 'convert-my-file'
                        }
                    }
                })

                print(f"✅ Job criado: {job['id']}")

                upload_task = job['tasks'][0]
                upload_url = upload_task['result']['form']['url']
                upload_params = upload_task['result']['form']['parameters']

                with open(filepath, 'rb') as f:
                    files = {'file': (filename, f)}
                    response = requests.post(upload_url, data=upload_params, files=files)
                    print(f"📤 Upload do ficheiro: {response.status_code}")

                print("⏳ A aguardar processamento do job...")
                job = cloudconvert_api.jobs.wait(id=job['id'])  # Esperar até o job acabar
                print(f"✅ Job finalizado: {job['status']}")

                export_task = [task for task in job['tasks'] if task['name'] == 'export-my-file'][0]
                file_url = export_task['result']['files'][0]['url']
                print(f"🔗 Link para download: {file_url}")

                output_path = os.path.join('/tmp', f"{os.path.splitext(filename)[0]}.jpg")
                r = requests.get(file_url, allow_redirects=True)
                with open(output_path, 'wb') as f:
                    f.write(r.content)
                print(f"✅ Ficheiro convertido e guardado: {output_path}")

                return send_file(output_path, as_attachment=True)

            except Exception as e:
                print(f"❌ Erro ao converter: {str(e)}")
                return f"Erro ao converter: {str(e)}", 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
