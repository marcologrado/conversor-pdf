from flask import Flask, request, render_template, send_file
import requests
import os

app = Flask(__name__)

# ========================
# ⚠️ API KEY DIRETA AQUI ⚠️
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"
# ========================


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    if 'pdf_file' not in request.files:
        return "Nenhum arquivo enviado", 400

    pdf_file = request.files['pdf_file']

    # Enviar o arquivo para o CloudConvert
    files = {'file': (pdf_file.filename, pdf_file.stream, pdf_file.mimetype)}
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }

    # Criar o job de conversão
    create_job_url = 'https://api.cloudconvert.com/v2/import/upload'
    response = requests.post(create_job_url, headers=headers)
    if response.status_code != 201:
        return f"Erro ao criar upload: {response.text}", 500

    upload_task = response.json()['data']
    upload_url = upload_task['result']['form']['url']
    upload_params = upload_task['result']['form']['parameters']

    # Enviar o arquivo para o link de upload
    upload_response = requests.post(upload_url, data=upload_params, files=files)
    if upload_response.status_code != 204:
        return f"Erro ao enviar arquivo: {upload_response.text}", 500

    # Criar tarefa de conversão
    convert_task_payload = {
        "tasks": {
            "import-upload": {
                "operation": "import/upload"
            },
            "convert": {
                "operation": "convert",
                "input": "import-upload",
                "input_format": "pdf",
                "output_format": "png"
            },
            "export-url": {
                "operation": "export/url",
                "input": "convert"
            }
        }
    }

    convert_job_url = 'https://api.cloudconvert.com/v2/jobs'
    convert_response = requests.post(convert_job_url, headers=headers, json=convert_task_payload)
    if convert_response.status_code != 201:
        return f"Erro ao criar job de conversão: {convert_response.text}", 500

    job_data = convert_response.json()['data']

    return f"Conversão iniciada! Job ID: {job_data['id']}"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
