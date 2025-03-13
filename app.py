import os
import cloudconvert
import requests
from flask import Flask, request, render_template, send_file

app = Flask(__name__)

# API KEY DIRETA NO CÓDIGO
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"

# Inicializar CloudConvert
cloudconvert.configure(api_key=API_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            input_filepath = os.path.join('uploads', file.filename)
            output_filepath = os.path.join('outputs', file.filename.replace('.pdf', '.png'))
            
            os.makedirs('uploads', exist_ok=True)
            os.makedirs('outputs', exist_ok=True)

            file.save(input_filepath)

            try:
                # Cria Job CloudConvert
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
                            "pages": "1",
                        },
                        'export-my-file': {
                            'operation': 'export/url',
                            'input': 'convert-my-file'
                        }
                    }
                })

                print("✅ JOB criado:", job['id'])

                # Upload do ficheiro
                upload_task = job['tasks'][0]  # import-my-file
                upload_url = upload_task['result']['form']['url']
                upload_parameters = upload_task['result']['form']['parameters']

                print("🔗 URL do upload:", upload_url)
                print("📦 Parâmetros:", upload_parameters)

                with open(input_filepath, 'rb') as f:
                    files = {'file': (file.filename, f)}
                    response = requests.post(
                        upload_url,
                        data=upload_parameters,
                        files=files
                    )

                print("📤 Status do Upload:", response.status_code)
                print("📤 Resposta do Upload:", response.text)

                if response.status_code not in [200, 201]:
                    return "Erro no upload do arquivo!", 400

                return "Upload e Job criado com sucesso! Aguarde processamento."
            
            except Exception as e:
                print("❌ Erro completo:", str(e))
                return f"Ocorreu um erro: {e}", 500

    return '''
    <!doctype html>
    <title>Conversor PDF para PNG</title>
    <h1>Upload PDF</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
