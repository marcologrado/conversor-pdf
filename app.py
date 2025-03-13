from flask import Flask
import cloudconvert
import os

app = Flask(__name__)

# ⚠️ API Key que me enviaste (NÃO partilhar com ninguém fora deste projeto!)
CLOUDCONVERT_API_KEY = "VgJ***********2v0"  # <-- Aqui vai tua API Key real (resumo por segurança)
cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)

@app.route('/')
def index():
    return '''
        <h1>✅ Teste de ligação com CloudConvert</h1>
        <p><a href="/testar" style="font-size:20px; color:green;">Clique aqui para testar criar um Job no CloudConvert</a></p>
    '''

@app.route('/testar')
def testar_cloudconvert():
    try:
        # Criar um Job "vazio" só para testar a comunicação com API
        job = cloudconvert.Job.create(payload={
            "tasks": {
                'import-1': {
                    'operation': 'import/upload'
                },
                'convert-1': {
                    'operation': 'convert',
                    'input': 'import-1',
                    'input_format': 'pdf',
                    'output_format': 'jpg',
                    "output_format": "jpg"
                },
                'export-1': {
                    'operation': 'export/url',
                    'input': 'convert-1'
                }
            }
        })

        # Mostrar o resultado na tela
        return f"<h2>✅ Job criado com sucesso!</h2><p><strong>ID do Job:</strong> {job['id']}</p>"
    
    except Exception as e:
        # Mostrar o erro, se houver
        return f"<h2>❌ Erro ao criar Job</h2><p>{str(e)}</p>"

if __name__ == '__main__':
    app.run(debug=True)
