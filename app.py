import os
from flask import Flask, render_template, request, send_file, redirect, url_for
import cloudconvert
import tempfile
import shutil

app = Flask(__name__)

# ⚠️ API KEY do CloudConvert
CLOUDCONVERT_API_KEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZmI2NDBjYmU0YmQ2YWIwZjE2MTQxMzI0NGVmOTI1ODZmOTZlMDRmMDYxMzI2Y2UxODM2NTM1ZTRjZmViNTI0ZDRmNTE1ODMwZmVkMmQzOTkiLCJpYXQiOjE3NDE3OTI0NzUuMzY4MTksIm5iZiI6MTc0MTc5MjQ3NS4zNjgxOTEsImV4cCI6NDg5NzQ2NjA3NS4zNjM0MjQsInN1YiI6IjcxMzEzMTg1Iiwic2NvcGVzIjpbInRhc2sucmVhZCIsInRhc2sud3JpdGUiXX0.PgcpeI7lQk9hegNbtYR4tq7anxEtXhgTWuXv9nBtFtVlxqzKuG_mqUpYLpFyrkJ_UJCy4PLQdVC6r99cWcgwrGdBb9XyduPETjNT4Mf1KId0qPMJaUaiAs32zBvuN_BRSQX2hgZAGITFctHyau_pDvdH5xqwDL1dwAUjM784xhhhurQhirAiNE71TSI_3ce-SU-yX5cZbbqos7_O5ot_U5HR1y5BbeJ1QxzXhcIekQppSner2rjwMQYB8ooCTLAzokFHScwK4QKU8o9SsOKrIzvdTscSROxmI2GEFxjGGilpDmd_6yntBRepnoDersmTKNbemTvhSpPh2Cw6kInqvz3InMOfNVdPyPb0DUP-SG8Seg_z8G9O9ldqy1Gp_-9rT-45govNkjeBdW-ZcNuF950-_bVA1pRriX8vHYJDpta7e8VWF7GOReEh3vnPZtqVOLDDcle5vX193OKkkrxu-TFisgUXl4nFHzefdD8Izx0E4cG2geS3nrd1ipZU9Ff1OkTDMuL0Qgzd1K2oLxRLaB7gtMyi1ElUVxXbBi9GjflJWAC5dIx22fxJ8a1wW4NyIh6UoFYr-s-KLSLpQRvQ9LUZYXChg8XpjMeQysYIQxTOBO_C-Wv4w02ESqRWtlE_sS1MJ4jueRq46DjP0BSRLJDpEuocZKuHj-_O7zZ29gQ'

cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY, sandbox=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return redirect(request.url)
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return redirect(request.url)

        temp_dir = tempfile.mkdtemp()
        input_pdf_path = os.path.join(temp_dir, pdf_file.filename)
        pdf_file.save(input_pdf_path)

        filename_without_ext = os.path.splitext(pdf_file.filename)[0]
        output_dir = os.path.join(temp_dir, filename_without_ext)
        os.makedirs(output_dir, exist_ok=True)

        # Converte para PNG
        job_png = cloudconvert.Job.create(payload={
            "tasks": {
                'import-my-file': {
                    'operation': 'import/upload'
                },
                'convert-my-file': {
                    'operation': 'convert',
                    'input': 'import-my-file',
                    'output_format': 'png',
                    'engine': 'office',
                    'engine_version': '1.0'
                },
                'export-my-file': {
                    'operation': 'export/url',
                    'input': 'convert-my-file'
                }
            }
        })

        upload_task_png = job_png['tasks'][0]
        upload_url_png = upload_task_png['result']['form']['url']
        cloudconvert.Task.upload(file_name=input_pdf_path, task=upload_task_png)

        job_png = cloudconvert.Job.wait(id=job_png['id'])
        export_task_png = [task for task in job_png['tasks'] if task['name'] == 'export-my-file'][0]
        file_url_png = export_task_png['result']['files'][0]['url']

        # Converte para JPG
        job_jpg = cloudconvert.Job.create(payload={
            "tasks": {
                'import-my-file': {
                    'operation': 'import/upload'
                },
                'convert-my-file': {
                    'operation': 'convert',
                    'input': 'import-my-file',
                    'output_format': 'jpg',
                    'engine': 'office',
                    'engine_version': '1.0'
                },
                'export-my-file': {
                    'operation': 'export/url',
                    'input': 'convert-my-file'
                }
            }
        })

        upload_task_jpg = job_jpg['tasks'][0]
        upload_url_jpg = upload_task_jpg['result']['form']['url']
        cloudconvert.Task.upload(file_name=input_pdf_path, task=upload_task_jpg)

        job_jpg = cloudconvert.Job.wait(id=job_jpg['id'])
        export_task_jpg = [task for task in job_jpg['tasks'] if task['name'] == 'export-my-file'][0]
        file_url_jpg = export_task_jpg['result']['files'][0]['url']

        shutil.rmtree(temp_dir)
        
        return render_template('index.html', file_url_png=file_url_png, file_url_jpg=file_url_jpg)

    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
