import os
from flask import Flask, request, render_template, redirect, send_file
from cloudconvert import Client
import uuid
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# ⚙️ Carregar API Key do CloudConvert
CLOUDCONVERT_API_KEY = os.getenv('CLOUDCONVERT_API_KEY', 'A_TUA_API_KEY_AQUI')
print(f"🔑 API KEY carregada: {bool(CLOUDCONVERT_API_KEY)}")

cloudconvert_api = Client(api_key=CLOUDCONVERT_API_KEY)

# ⚙️ Configurar logging (opcional, para debug)
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return 'Nenhum arquivo enviado', 400

        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return 'Nenhum arquivo selecionado', 400

        # Gerar um nome único
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{pdf_file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Garantir que a pasta de uploads existe
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Salvar o arquivo
        pdf_file.save(file_path)

        try:
            logging.info(f"🚀 Enviando arquivo para CloudConvert: {file_path}")

            # Criar o job no CloudConvert
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
                        'engine': 'office',  # pode tentar 'office' ou 'openoffice'
                        'pages': '1-1',  # opcional: ajustar páginas
                        'pixel_density': 300,
                        'output': {
                            'type': 'image/png'
                        }
                    },
                    'export-my-file': {
                        'operation': 'export/url',
                        'input': 'convert-my-file'
                    }
                }
            })

            logging.info(f"✅ Job criado: {job['id']}")

            # Obter o link para upload
            upload_task = job['tasks'][0]
            upload_url = upload_task['result']['form']['url']
            upload_params = upload_task['result']['form']['parameters']

            # Fazer o upload para a URL do CloudConvert
            with open(file_path, 'rb') as f:
                upload_files = {'file': (pdf_file.filename, f)}
                response = cloudconvert_api.tasks.upload(file=upload_files, **upload_params)

            logging.info(f"✅ Upload completo para o CloudConvert: {response}")

            # Agora esperar a conclusão do job (podes colocar async para não travar o servidor)
            # Aqui assume que o processo é rápido
            export_task = cloudconvert_api.tasks.wait(id=job['tasks'][2]['id'])  # export-my-file
            file_url = export_task['result']['files'][0]['url']

            logging.info(f"📁 Link do ficheiro convertido: {file_url}")

            # Redirecionar para o download do ficheiro
            return redirect(file_url)

        except Exception as e:
            logging.error(f"❌ Erro ao converter: {e}")
            return f"Erro na conversão: {str(e)}", 500

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
