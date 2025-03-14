from flask import Flask, request, render_template_string
import cloudconvert
import os

app = Flask(__name__)

# ✅ API KEY direta
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"
cloudconvert_api = cloudconvert.Client(api_key=API_KEY)

# ✅ HTML simples
UPLOAD_FORM_HTML = '''
<!doctype html>
<title>Conversor de PDF</title>
<h1>Enviar PDF</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Enviar>
</form>
'''

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            return "Erro ao enviar o arquivo!"

        # ✅ Job correto com PNG e JPG, redimensionados conforme pedido
        job = cloudconvert_api.jobs.create(payload={
            "tasks": {
                'import-file': {
                    'operation': 'import/upload'
                },
                'convert-png': {
                    'operation': 'convert',
                    'input': 'import-file',
                    'input_format': 'pdf',
                    'output_format': 'png',
                    'pages': '1-',
                    'engine': 'office',
                    'engine_version': '1.0',
                    'output': {
                        "fit": "max",
                        "height": 3070  # Altura máxima do PNG
                    }
                },
                'convert-jpg': {
                    'operation': 'convert',
                    'input': 'import-file',
                    'input_format': 'pdf',
                    'output_format': 'jpg',
                    'pages': '1-',
                    'engine': 'office',
                    'engine_version': '1.0',
                    'output': {
                        "fit": "max",
                        "height": 90  # Altura máxima do JPG
                    }
                },
                'export-png': {
                    'operation': 'export/url',
                    'input': 'convert-png'
                },
                'export-jpg': {
                    'operation': 'export/url',
                    'input': 'convert-jpg'
                }
            }
        })

        # ✅ Pega URL de upload
        upload_task = [task for task in job['tasks'] if task['name'] == 'import-file'][0]
        upload_url = upload_task['result']['form']['url']
        upload_params = upload_task['result']['form']['parameters']

        # ✅ Faz upload real
        files = {'file': (file.filename, file.stream, file.mimetype)}
        response = cloudconvert.multipart.upload(url=upload_url, files=files, parameters=upload_params)

        return "Upload com sucesso! Aguardando conversão. Consulta o CloudConvert para os links finais."
    return render_template_string(UPLOAD_FORM_HTML)

# ✅ Corre o app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
