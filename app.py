import os
from flask import Flask, request, jsonify
import cloudconvert

app = Flask(__name__)

# === CONFIGURAÇÃO CLOUDCONVERT ===
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"
cloudconvert.configure(api_key=API_KEY, sandbox=False)

# Dicionário para simular base de dados temporária (podes trocar por um banco real)
jobs_status = {}


# === ROTA PARA UPLOAD E CRIAÇÃO DO JOB ===
@app.route('/', methods=['POST'])
def upload_file():
    file = request.files['file']
    if not file:
        return 'Erro: Nenhum arquivo enviado!', 400

    # Nome do arquivo temporário
    filename = file.filename
    file.save(filename)

    # Criar o job na CloudConvert
    job = cloudconvert.Job.create(payload={
        "tasks": {
            'import-my-file': {
                'operation': 'import/upload'
            },
            'convert-png': {
                'operation': 'convert',
                'input': 'import-my-file',
                'input_format': 'pdf',
                'output_format': 'png',
                'engine': 'office',
                'engine_version': '4.0',
                'timeout': 300,
                'pdf': {
                    'pages': '1'
                },
                "output": {
                    "resize": {
                        "resize_mode": "fit",
                        "height": 3070
                    }
                }
            },
            'convert-jpg': {
                'operation': 'convert',
                'input': 'import-my-file',
                'input_format': 'pdf',
                'output_format': 'jpg',
                'engine': 'office',
                'engine_version': '4.0',
                'timeout': 300,
                'pdf': {
                    'pages': '1'
                },
                "output": {
                    "resize": {
                        "resize_mode": "fit",
                        "height": 90
                    }
                }
            },
            'export-my-file': {
                'operation': 'export/url',
                'input': ['convert-png', 'convert-jpg']
            }
        },
        "tag": "conversao_pdf",
        "webhook": "https://teu_dominio.onrender.com/webhook"
    })

    # Guardar o status inicial
    jobs_status[job['id']] = 'Processando'

    # Upload do arquivo
    upload_task = job['tasks'][0]
    upload_url = upload_task['result']['form']['url']
    upload_parameters = upload_task['result']['form']['parameters']
    with open(filename, 'rb') as f:
        requests.post(upload_url, data=upload_parameters, files={'file': f})

    os.remove(filename)

    return jsonify({'message': 'Conversão iniciada.', 'job_id': job['id']}), 200


# === WEBHOOK PARA RECEBER RESULTADO FINAL ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    job_id = data['job']['id']
    status = data['job']['status']

    if status == 'finished':
        # Pega os links dos arquivos convertidos
        export_task = next(task for task in data['job']['tasks'] if task['operation'] == 'export/url')
        files = export_task['result']['files']

        # Guardar no "banco"
        jobs_status[job_id] = {
            'status': 'Concluído',
            'files': [{'filename': file['filename'], 'url': file['url']} for file in files]
        }
    else:
        jobs_status[job_id] = {'status': status}

    return '', 200


# === CONSULTAR STATUS DO JOB ===
@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    job_info = jobs_status.get(job_id, None)
    if not job_info:
        return jsonify({'status': 'Não encontrado'}), 404
    return jsonify(job_info), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
