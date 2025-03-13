from flask import Flask, render_template, request
import os
import cloudconvert
import requests

app = Flask(__name__)

# API KEY DIRETA NO CÓDIGO
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"

cloudconvert.configure(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    # Salvar temporariamente o arquivo
    input_filepath = os.path.join('uploads', file.filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(input_filepath)

    try:
        # Criar job na CloudConvert
        job = cloudconvert.Job.create(payload={
            "tasks": {
                'import-my-file': {
                    'operation': 'import/upload'
                },
                'convert-my-file': {
                    'operation': 'convert',
                    'input': 'import-my-file',
                    'output_format': 'png'
                },
                'export-my-file': {
                    'operation': 'export/url',
                    'input': 'convert-my-file'
                }
            }
        })

        # Obter tarefa de upload
        upload_task = next(task for task in job['tasks'] if task['name'] == 'import-my-file')

        # Preparar upload correto
        upload_url = upload_task['result']['form']['url']
        form_data = upload_task['result']['form']['parameters']

        with open(input_filepath, 'rb') as f:
            files = {'file': (file.filename, f)}
            response = requests.post(upload_url, data=form_data, files=files)

        print("⚙️ Upload response:", response.status_code, response.text)  # Log para debug

        if response.status_code == 201 or response.status_code == 200:
            return 'Arquivo enviado e conversão iniciada com sucesso!'
        else:
            return f'Erro no upload do arquivo! {response.status_code} - {response.text}'

    except Exception as e:
        print(f"❌ Erro no processo: {e}")
        return f'Erro: {e}'

if __name__ == '__main__':
    app.run(debug=True)
