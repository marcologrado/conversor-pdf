from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# ====================== CONFIGURAÇÃO ===========================
# ✅ API KEY DIRETA NO CÓDIGO (como combinámos)
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"
# ==============================================================

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            # 1. Criar o Job no CloudConvert
            create_job_url = "https://api.cloudconvert.com/v2/jobs"
            payload = {
                "tasks": {
                    "import-file": {
                        "operation": "import/upload"
                    },
                    "convert-file": {
                        "operation": "convert",
                        "input": "import-file",
                        "output_format": "jpg"
                    },
                    "export-file": {
                        "operation": "export/url",
                        "input": "convert-file"
                    }
                }
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            job_response = requests.post(create_job_url, json=payload, headers=headers)

            if job_response.status_code != 201:
                return "Erro ao criar job no CloudConvert!"

            job_data = job_response.json()
            job_id = job_data["data"]["id"]
            upload_task = next(task for task in job_data["data"]["tasks"] if task["name"] == "import-file")
            upload_url = upload_task["result"]["form"]["url"]
            upload_params = upload_task["result"]["form"]["parameters"]

            # 2. Fazer o upload do arquivo
            upload_files = {'file': (file.filename, file.stream, file.mimetype)}
            upload_response = requests.post(upload_url, data=upload_params, files=upload_files)

            if upload_response.status_code != 201:
                return "Erro ao fazer upload do arquivo!"

            # 3. Esperar o job finalizar (simples polling)
            status = "waiting"
            while status not in ["finished", "error"]:
                job_status_response = requests.get(f"https://api.cloudconvert.com/v2/jobs/{job_id}", headers=headers)
                job_status_data = job_status_response.json()
                status = job_status_data["data"]["status"]

            if status == "error":
                return "Erro na conversão do arquivo!"

            # 4. Obter o URL de download
            export_task = next(
                task for task in job_status_data["data"]["tasks"]
                if task["name"] == "export-file" and task["status"] == "finished"
            )
            file_url = export_task["result"]["files"][0]["url"]

            return f'<a href="{file_url}" target="_blank">Download do arquivo convertido</a>'

    # HTML simples para o upload
    return render_template_string('''
    <!doctype html>
    <title>Conversor de PDF para JPG</title>
    <h1>Upload do PDF</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    ''')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
