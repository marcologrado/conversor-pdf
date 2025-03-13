import os
from flask import Flask, render_template_string, request, redirect, url_for, send_file
import requests
import tempfile

app = Flask(__name__)

# ⚠️ TUA API KEY DIRETA NO CÓDIGO
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"

# Página simples para upload
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Conversor PDF para JPG</title></head>
<body>
    <h1>Upload de PDF para Converter em JPG</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="pdf_file" accept="application/pdf" required>
        <button type="submit">Converter</button>
    </form>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']

        if not pdf_file:
            return "Nenhum arquivo enviado!", 400

        # 1. Criar job no CloudConvert
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        job_payload = {
            "tasks": {
                "import-file": {
                    "operation": "import/upload"
                },
                "convert-file": {
                    "operation": "convert",
                    "input": "import-file",
                    "input_format": "pdf",
                    "output_format": "jpg",
                    "pages": "1"  # ou "1-" para todas as páginas
                },
                "export-file": {
                    "operation": "export/url",
                    "input": "convert-file"
                }
            }
        }

        job_response = requests.post("https://api.cloudconvert.com/v2/jobs", headers=headers, json=job_payload)
        job_data = job_response.json()

        try:
            upload_task = next(task for task in job_data['data']['tasks'] if task['name'] == 'import-file')
            upload_url = upload_task['result']['form']['url']
            upload_params = upload_task['result']['form']['parameters']
        except Exception as e:
            return f"Erro ao preparar o upload: {e}"

        # 2. Fazer upload do arquivo
        files = {'file': (pdf_file.filename, pdf_file.stream, pdf_file.mimetype)}
        upload_response = requests.post(upload_url, data=upload_params, files=files)

        if upload_response.status_code != 204:
            return "Erro no upload do arquivo!", 500

        # 3. Aguardar o job terminar
        job_id = job_data['data']['id']
        while True:
            job_status = requests.get(f"https://api.cloudconvert.com/v2/jobs/{job_id}", headers=headers).json()
            status = job_status['data']['status']
            if status == 'finished':
                break
            elif status == 'error':
                return "Erro na conversão!", 500

        # 4. Buscar link de download
        export_task = next(task for task in job_status['data']['tasks'] if task['name'] == 'export-file')
        file_url = export_task['result']['files'][0]['url']

        # 5. Baixar e entregar o JPG final
        final_file = requests.get(file_url)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(final_file.content)
        temp_file.close()

        return send_file(temp_file.name, as_attachment=True, download_name="convertido.jpg")

    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
