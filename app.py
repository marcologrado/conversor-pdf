import os
from flask import Flask, request, render_template_string
import cloudconvert

app = Flask(__name__)

# ✅ API KEY DIRETA NO CÓDIGO (conforme combinámos)
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmEyMDVlNzczMGUyMzFlYTJmZmY5YjI2ODFlZGY4Mzg4MDkzYTI4NDI2ZWI5ZmE1ZTRiNGU2ODQ1YmVjODRmZGQ5MzYxZDVhNGIxMGE4NWEiLCJpYXQiOjE3NDE5MDc1NjkuNzcyNzgzLCJuYmYiOjE3NDE5MDc1NjkuNzcyNzg0LCJleHAiOjQ4OTc1ODExNjkuNzY3OTU3LCJzdWIiOiI3MTMxMzE4NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIiwidXNlci5yZWFkIl19.VbIhpkWns0dQCKQ1VVujM4xt065W9lWGjKvLzj0jir3jIPtiwQxJBwkDHdNMNRtYBwqPTWXshaa5erPcMRFXLlhB2kmisosdc5auTIyvDgW0V4t4oOz2qluiHNULygBWFbMnNLGSCgAfgd5Ufrw022Jl9ykdCYJwDu2a2amytOGd4tP9PIO_LBxQ4ebMCRmH14mfV0d61aT1qtfU1DU03tXQSCCoFTqMuGdiPakZur8ilpJcsdaGhpyjNYUKl84DlTp8uxnhmzfc64hEaDWJtifDHO2eiaNi1FO3U8Q-6G28kPGec2euvWYt61UfvZ2JGu_h10dC45NJmQk-DMRJsNkm0pUcD6Z7IuEb7UfBkeSYldNb1r48kpS4ftI4L4YHQdH2t6wPU-9g5gLB6UPVLlSKYcQcn1RhCwemGIHvt3RtArL_tHB_ni_rnyCp8jmGK6STRpsnjuyJCgfN60SmNP0rRl1s2vl9n_Jolp65GU3osnNeQBQJPBTBD67h88t9tXvdKOJgrJW20cf3I8h-tG7FYFlPKw6pcoLgTJkbzcuLGVHaMAl4VLaMyWiPSYWLgXIrCNsfOl4J3jVWMxFjarg5n689l8Qw-BsecHf2oNdLDi6Ue1vJwmrl0b0d0RcQ_NBRbuWZ66Xg8Ff556JNghzNEr-qO2C08THMx3848Yw"

cloudconvert.configure(api_key=API_KEY, sandbox=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]

        if file:
            # ✅ Criação do job completo
            job_payload = {
                "tasks": {
                    "import-my-file": {
                        "operation": "import/upload"
                    },
                    "convert-my-file": {
                        "operation": "convert",
                        "input": "import-my-file",
                        "input_format": "pdf",
                        "output_format": "jpg"
                    },
                    "export-my-file": {
                        "operation": "export/url",
                        "input": "convert-my-file"
                    }
                }
            }

            job = cloudconvert.Job.create(payload=job_payload)
            upload_task = next(task for task in job['tasks'] if task['name'] == 'import-my-file')

            # ✅ Upload do ficheiro para CloudConvert
            upload = cloudconvert.Task.upload(file=file, task=upload_task)

            print(f"✅ Upload completo: {upload}")

            # ✅ Atualiza o job para esperar a conversão e exportação
            job = cloudconvert.Job.find(id=job['id'])

            # ✅ Captura URL final
            export_task = next(task for task in job['tasks'] if task['name'] == 'export-my-file')
            file_url = export_task['result']['files'][0]['url']

            print(f"🎉 URL para download: {file_url}")

            # ✅ Devolve link na página
            return render_template_string('''
                <h1>Conversão Concluída!</h1>
                <p><a href="{{ url }}" target="_blank">Clique aqui para fazer o download do seu ficheiro convertido</a></p>
            ''', url=file_url)

        return "Erro no upload do arquivo!"

    # Página inicial com formulário
    return '''
        <h1>Conversor de PDF para JPG</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="application/pdf">
            <input type="submit" value="Converter">
        </form>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
