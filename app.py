from flask import Flask, render_template_string, request, redirect, send_file
import cloudconvert
import os
import requests

app = Flask(__name__)

# ================================
# API KEY DIRETA NO CÓDIGO (Atenção à segurança em ambiente de produção)
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"
cloudconvert.configure(api_key=API_KEY)

# ================================

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return 'Nenhum arquivo enviado!'
        pdf_file = request.files['pdf_file']

        # Upload do arquivo
        try:
            job = cloudconvert.Job.create(payload={
                "tasks": {
                    'import-my-file': {
                        'operation': 'import/upload'
                    },
                    'convert-my-file': {
                        'operation': 'convert',
                        'input': 'import-my-file',
                        'input_format': 'pdf',
                        'output_format': 'png',
                        "engine": "office",
                        "engine_version": "1.0"
                    },
                    'export-my-file': {
                        'operation': 'export/url',
                        'input': 'convert-my-file'
                    }
                }
            })

            # Obter URL de upload
            upload_task_id = job['tasks'][0]['id']
            upload_task = cloudconvert.Task.find(id=upload_task_id)
            upload_url = upload_task['result']['form']['url']
            upload_parameters = upload_task['result']['form']['parameters']

            # Fazer upload do arquivo para a URL
            files = {'file': (pdf_file.filename, pdf_file.stream, pdf_file.mimetype)}
            response = requests.post(upload_url, data=upload_parameters, files=files)

            if response.status_code != 204:
                return 'Erro ao fazer upload do arquivo!'

            # Esperar a conversão finalizar
            job = cloudconvert.Job.wait(id=job['id'])

            # Obter o link do arquivo convertido
            export_task = next(task for task in job['tasks'] if task['name'] == 'export-my-file')
            file_url = export_task['result']['files'][0]['url']

            # Download automático
            response = requests.get(file_url)
            output_file = 'output.png'
            with open(output_file, 'wb') as f:
                f.write(response.content)

            return send_file(output_file, as_attachment=True)

        except Exception as e:
            print(f"Erro: {e}")
            return 'Erro no processo de conversão!'
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Conversor PDF para PNG</title>
        </head>
        <body>
            <h1>Converter PDF em PNG</h1>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="pdf_file" accept="application/pdf" required>
                <button type="submit">Converter</button>
            </form>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.getenv("PORT", 5000))
