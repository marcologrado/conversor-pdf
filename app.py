from flask import Flask, render_template_string, request
import requests
import time

app = Flask(__name__)

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Criação do job
            job_payload = {
                "tasks": {
                    "import-my-file": {"operation": "import/upload"},
                    "convert-to-png": {
                        "operation": "convert",
                        "input": ["import-my-file"],
                        "input_format": "pdf",
                        "output_format": "png",
                        "engine": "office",
                        "output": {"resize": {"resize_mode": "fit", "height": 3070}}
                    },
                    "convert-to-jpg": {
                        "operation": "convert",
                        "input": ["import-my-file"],
                        "input_format": "pdf",
                        "output_format": "jpg",
                        "engine": "office",
                        "output": {"resize": {"resize_mode": "fit", "height": 90}}
                    },
                    "export-png": {"operation": "export/url", "input": ["convert-to-png"]},
                    "export-jpg": {"operation": "export/url", "input": ["convert-to-jpg"]}
                }
            }

            job_response = requests.post(
                'https://api.cloudconvert.com/v2/jobs',
                json=job_payload,
                headers={'Authorization': f'Bearer {API_KEY}'}
            ).json()

            # Upload
            upload_task = [t for t in job_response['data']['tasks'] if t['name'] == 'import-my-file'][0]
            upload_url = upload_task['result']['form']['url']
            upload_params = upload_task['result']['form']['parameters']
            requests.post(upload_url, data=upload_params, files={'file': (file.filename, file.stream)})

            job_id = job_response['data']['id']

            # Polling - Aguarda até o job estar COMPLETO
            while True:
                job_status = requests.get(
                    f'https://api.cloudconvert.com/v2/jobs/{job_id}',
                    headers={'Authorization': f'Bearer {API_KEY}'}
                ).json()
                if job_status['data']['status'] == 'finished':
                    break
                time.sleep(5)  # Espera 5 segundos antes de tentar novamente

            # Obter links finais
            export_tasks = [t for t in job_status['data']['tasks'] if t['operation'] == 'export/url']
            download_links = []
            for task in export_tasks:
                if 'result' in task and 'files' in task['result']:
                    for f in task['result']['files']:
                        download_links.append(f['url'])

            return render_template_string('''
                <h1>Conversão finalizada com sucesso!</h1>
                <ul>
                    {% for link in links %}
                    <li><a href="{{ link }}" target="_blank">Download</a></li>
                    {% endfor %}
                </ul>
                <a href="/">Voltar</a>
            ''', links=download_links)

    return '''
    <!doctype html>
    <title>Conversor de PDF</title>
    <h1>Enviar PDF</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file required>
      <input type=submit value=Converter>
    </form>
    '''

if __name__ == '__main__':
    app.run(debug=True)
