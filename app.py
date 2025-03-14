from flask import Flask, request, render_template_string
import cloudconvert
import requests

app = Flask(__name__)

# ✅ API KEY COMPLETA DIRETA (para testes apenas)
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"

cloudconvert_api = cloudconvert.Api(API_KEY)

HTML = '''
<!DOCTYPE html>
<html>
<head><title>Conversor PDF para PNG</title></head>
<body>
    <h1>Conversor de PDF para PNG</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".pdf" required>
        <button type="submit">Converter</button>
    </form>
    {% if download_url %}
        <p><a href="{{ download_url }}" target="_blank">Download do PNG</a></p>
    {% endif %}
    {% if error %}
        <p style="color:red;">Erro: {{ error }}</p>
    {% endif %}
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if file:
            try:
                # 1. Criar o Job completo
                job = cloudconvert_api.jobs.create(payload={
                    "tasks": {
                        "import-file": {"operation": "import/upload"},
                        "convert-file": {
                            "operation": "convert",
                            "input": "import-file",
                            "output_format": "png"
                        },
                        "export-file": {
                            "operation": "export/url",
                            "input": "convert-file"
                        }
                    }
                })
                print("✅ Job criado:", job["id"])

                # 2. Upload do arquivo
                upload_task = job["tasks"][0]
                upload_url = upload_task["result"]["form"]["url"]
                upload_params = upload_task["result"]["form"]["parameters"]
                print("✅ URL do Upload:", upload_url)

                files = {'file': (file.filename, file.stream, file.content_type)}
                response = requests.post(upload_url, data=upload_params, files=files)
                print("✅ Upload Response:", response.status_code, response.text)

                if response.status_code != 201:
                    return render_template_string(HTML, error="Erro ao fazer upload do arquivo!")

                # 3. Verificar se o processo finalizou
                job = cloudconvert_api.jobs.get(job["id"])
                export_task = next(task for task in job["tasks"] if task["name"] == "export-file")
                print("✅ Estado do export:", export_task["status"])

                if export_task["status"] != "finished":
                    return render_template_string(HTML, error="Conversão ainda não terminou, tente novamente.")

                # 4. Pegar link do download
                download_url = export_task["result"]["files"][0]["url"]
                print("✅ URL final:", download_url)

                return render_template_string(HTML, download_url=download_url)

            except Exception as e:
                print("❌ Erro geral:", e)
                return render_template_string(HTML, error=f"Ocorreu um erro: {str(e)}")
        else:
            return render_template_string(HTML, error="Nenhum arquivo enviado.")
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
