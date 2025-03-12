import os
from flask import Flask, render_template, request, send_file
import cloudconvert
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# CloudConvert API KEY
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")
print(f"🔑 API KEY carregada: {bool(CLOUDCONVERT_API_KEY)}")

# Inicializar CloudConvert
cloudconvert_api = cloudconvert.Client(api_key=CLOUDCONVERT_API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = file.filename
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            print(f"📁 Ficheiro recebido: {upload_path}")

            # Nome base para a pasta e arquivos
            base_name = os.path.splitext(filename)[0]
            output_dir = os.path.join(app.config['UPLOAD_FOLDER'], base_name)
            os.makedirs(output_dir, exist_ok=True)

            # Criar Job na CloudConvert
            print("🚀 A iniciar conversão na CloudConvert...")
            try:
                job = cloudconvert_api.jobs.create(payload={
                    "tasks": {
                        'import-my-file': {
                            'operation': 'import/upload'
                        },
                        'convert-my-file-png': {
                            'operation': 'convert',
                            'input': 'import-my-file',
                            'output_format': 'png',
                            'engine': 'office',
                            'engine_version': 'default'
                        },
                        'convert-my-file-jpg': {
                            'operation': 'convert',
                            'input': 'import-my-file',
                            'output_format': 'jpg',
                            'engine': 'office',
                            'engine_version': 'default'
                        },
                        'export-my-file': {
                            'operation': 'export/url',
                            'input': ['convert-my-file-png', 'convert-my-file-jpg'],
                            'inline': False,
                            'archive_multiple_files': False
                        }
                    }
                })

                print(f"✅ Job criado: {job['id']}")
                upload_task = job['tasks'][0]
                upload_url = upload_task['result']['form']['url']

                # Fazer upload do ficheiro
                with open(upload_path, 'rb') as file_data:
                    cloudconvert_api.tasks.upload(upload_task, file_data)
                print("✅ Upload para CloudConvert concluído.")

                # Verificar estado do job até estar concluído
                while True:
                    job = cloudconvert_api.jobs.get(job['id'])
                    status = job['status']
                    print(f"🔄 Status do job: {status}")
                    if status == 'finished':
                        break
                    elif status == 'error':
                        print("❌ Erro ao processar o ficheiro na CloudConvert.")
                        return "Erro na conversão", 500
                    time.sleep(5)

                # Obter URLs dos ficheiros convertidos
                export_task = next(task for task in job['tasks'] if task['name'] == 'export-my-file')
                files = export_task['result']['files']
                print(f"📤 Ficheiros convertidos: {[file['filename'] for file in files]}")

                # Fazer download dos ficheiros convertidos
                for file_info in files:
                    file_url = file_info['url']
                    output_path = os.path.join(output_dir, file_info['filename'])
                    os.system(f"curl -L {file_url} -o {output_path}")
                    print(f"⬇️  Ficheiro descarregado: {output_path}")

                # Retornar um dos ficheiros como exemplo
                return send_file(output_path, as_attachment=True)

            except Exception as e:
                print(f"❌ Erro na integração com CloudConvert: {e}")
                return "Erro ao processar o ficheiro", 500

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
