import os
import sys
import time as _time
import threading
from datetime import date, datetime
from functools import wraps

# Garante que o diretório backend está no path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import database as db
import whatsapp as wa
import scheduler

app = Flask(__name__, static_folder=None)

# ── Rate Limiter (in-memory) ──────────────────────────────────────────────────
_rate_store = {}   # { ip: [timestamp, timestamp, ...] }
_rate_lock = threading.Lock()

def rate_limit(max_calls, window_secs):
    """Decorator: limita chamadas por IP."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or '0.0.0.0'
            key = f'{f.__name__}:{ip}'
            now = _time.time()

            with _rate_lock:
                calls = _rate_store.get(key, [])
                # Remove timestamps fora da janela
                calls = [t for t in calls if now - t < window_secs]

                if len(calls) >= max_calls:
                    return jsonify({
                        'ok': False,
                        'msg': 'Muitas requisições. Tente novamente em breve.'
                    }), 429

                calls.append(now)
                _rate_store[key] = calls

            return f(*args, **kwargs)
        return wrapper
    return decorator

# ── CORS manual (sem flask-cors) ──────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return jsonify({}), 200

# ── Servir frontend ───────────────────────────────────────────────────────────
FRONTEND = os.path.join(os.path.dirname(__file__), '..', 'frontend')

@app.route('/')
def index():
    return send_from_directory(FRONTEND, 'form.html')

@app.route('/admin')
def admin():
    return send_from_directory(FRONTEND, 'admin.html')

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(FRONTEND, 'assets'), filename)

# ── API: Cadastro ─────────────────────────────────────────────────────────────
@app.route('/api/cadastro', methods=['POST'])
@rate_limit(5, 60)
def cadastro():
    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    telefone = (data.get('telefone') or '').strip()
    nascimento = (data.get('nascimento') or '').strip() or None

    if not nome or not telefone:
        return jsonify({'ok': False, 'msg': 'Nome e telefone são obrigatórios.'}), 400

    ok, msg = db.cadastrar_membro(nome, telefone, nascimento)

    if ok:
        # Mensagem de boas-vindas ao cadastro
        config = db.get_config()
        primeiro = nome.split()[0]
        msg_bv = config.get('msg_boas_vindas_cadastro',
            f'Olá, {primeiro}! 🙏 Bem-vindo(a) à nossa família! Você receberá lembretes dos nossos cultos por aqui.')
        msg_bv = msg_bv.replace('{nome}', primeiro)
        wa.enviar_mensagem(telefone, msg_bv)

    return jsonify({'ok': ok, 'msg': msg})

# ── API: Webhook Evolution (respostas dos membros) ────────────────────────────
@app.route('/api/webhook', methods=['POST'])
@rate_limit(60, 60)
def webhook():
    data = request.json or {}

    # Evolution API envia eventos em diferentes formatos
    event = data.get('event', '')
    if event not in ('messages.upsert', 'MESSAGES_UPSERT'):
        return jsonify({'ok': True})

    try:
        msg_data = data.get('data', {})
        key = msg_data.get('key', {})

        # Ignora mensagens enviadas pelo bot
        if key.get('fromMe'):
            return jsonify({'ok': True})

        # Extrai o número do telefone
        telefone_raw = key.get('remoteJid', '').replace('@s.whatsapp.net', '')
        
        # Converte TODO o payload da mensagem numa string em minúsculo pra buscar as intenções.
        # Assim pegamos conversas normais, botões antigos E votos em Enquetes (Polls)
        import json
        payload_str = json.dumps(msg_data, ensure_ascii=False).lower()
        
        # Como Enquetes tem as opções "Estarei lá! 🙌" e "Não vou poder ir 😔",
        # procuramos diretamente por termos chave no JSON inteiro:
        texto = payload_str

        membro = db.buscar_membro_por_telefone(telefone_raw)
        if not membro:
            return jsonify({'ok': True})

        hoje = date.today().isoformat()
        config = db.get_config()
        primeiro = membro['nome'].split()[0]

        # Detecta intenção de resposta em qualquer lugar do JSON recebido
        confirmou = any(x in texto for x in ['"estarei lá', '"sim', 'estarei lá! 🙌', 'sim_'])
        negou = any(x in texto for x in ['"não vou', '"nao vou', '"não', 'não vou poder ir 😔', 'nao_'])

        if confirmou:
            db.registrar_resposta(membro['id'], hoje, 'sim')
            msg = config.get('msg_boas_vindas', 'Bem-vindo ao culto, {nome}! 🙏').replace('{nome}', primeiro)
            wa.enviar_mensagem(membro['telefone'], msg)

        elif negou:
            db.registrar_resposta(membro['id'], hoje, 'nao')
            youtube = config.get('youtube_channel', '')
            msg = config.get('msg_ausente_pre', 'Sentimos sua falta, {nome}! Assista: {youtube}')
            msg = msg.replace('{nome}', primeiro).replace('{youtube}', youtube)
            wa.enviar_mensagem(membro['telefone'], msg)

    except Exception as e:
        print(f'[WEBHOOK] Erro: {e}')

    return jsonify({'ok': True})

# ── API: Painel ───────────────────────────────────────────────────────────────
@app.route('/api/painel')
@rate_limit(30, 60)
def painel():
    hoje = date.today().isoformat()
    membros = db.respostas_do_dia(hoje)

    confirmados = [m for m in membros if m.get('resposta') == 'sim']
    ausentes = [m for m in membros if m.get('resposta') == 'nao']
    aguardando = [m for m in membros if not m.get('resposta')]

    return jsonify({
        'data': hoje,
        'confirmados': confirmados,
        'ausentes': ausentes,
        'aguardando': aguardando,
    })

@app.route('/api/membros')
@rate_limit(30, 60)
def membros():
    return jsonify(db.listar_membros())

@app.route('/api/membros', methods=['POST'])
@rate_limit(5, 60)
def add_membro():
    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    telefone = (data.get('telefone') or '').strip()
    nascimento = (data.get('nascimento') or '').strip() or None
    if not nome or not telefone:
        return jsonify({'ok': False, 'msg': 'Nome e telefone obrigatórios.'}), 400
    ok, msg = db.cadastrar_membro(nome, telefone, nascimento)
    return jsonify({'ok': ok, 'msg': msg})

@app.route('/api/membros/<int:membro_id>', methods=['PUT'])
@rate_limit(10, 60)
def edt_membro(membro_id):
    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    telefone = (data.get('telefone') or '').strip()
    nascimento = (data.get('nascimento') or '').strip() or None
    ativo = data.get('ativo', True)
    
    if not nome or not telefone:
        return jsonify({'ok': False, 'msg': 'Nome e telefone obrigatórios.'}), 400
    
    ok, msg = db.atualizar_membro(membro_id, nome, telefone, nascimento, ativo)
    return jsonify({'ok': ok, 'msg': msg})

@app.route('/api/membros/<int:membro_id>', methods=['DELETE'])
@rate_limit(10, 60)
def del_membro(membro_id):
    ok, msg = db.deletar_membro(membro_id)
    return jsonify({'ok': ok, 'msg': msg})

@app.route('/api/config')
@rate_limit(30, 60)
def get_config():
    return jsonify(db.get_config())

@app.route('/api/config', methods=['POST'])
@rate_limit(10, 60)
def set_config():
    data = request.json or {}
    for chave, valor in data.items():
        db.set_config(chave, str(valor))
    return jsonify({'ok': True})

# ── API: Histórico ────────────────────────────────────────────────────────────
@app.route('/api/historico')
@rate_limit(30, 60)
def historico():
    inicio = request.args.get('inicio', '')
    fim = request.args.get('fim', '')
    if not inicio or not fim:
        # Padrão: últimos 30 dias
        from datetime import timedelta
        fim = date.today().isoformat()
        inicio = (date.today() - timedelta(days=30)).isoformat()
    dados = db.historico_por_periodo(inicio, fim)
    return jsonify({'inicio': inicio, 'fim': fim, 'dias': dados})

@app.route('/api/historico/<int:membro_id>')
@rate_limit(30, 60)
def historico_membro(membro_id):
    dados = db.historico_por_membro(membro_id)
    return jsonify(dados)

# ── API: Estatísticas ─────────────────────────────────────────────────────────
@app.route('/api/estatisticas')
@rate_limit(30, 60)
def estatisticas():
    return jsonify(db.estatisticas_gerais())

@app.route('/api/estatisticas/<int:membro_id>')
@rate_limit(30, 60)
def estatisticas_membro(membro_id):
    dados = db.estatisticas_membro(membro_id)
    if not dados:
        return jsonify({'ok': False, 'msg': 'Membro não encontrado.'}), 404
    return jsonify(dados)

# ── API: Disparos manuais (teste/emergência) ──────────────────────────────────
@app.route('/api/disparar/pre', methods=['POST'])
@rate_limit(2, 60)
def disparar_pre():
    import threading as t
    t.Thread(target=scheduler.disparar_pre_culto, daemon=True).start()
    return jsonify({'ok': True, 'msg': 'Pré-culto sendo disparado...'})

@app.route('/api/disparar/fim', methods=['POST'])
@rate_limit(2, 60)
def disparar_fim():
    import threading as t
    t.Thread(target=scheduler.disparar_fim_culto, daemon=True).start()
    return jsonify({'ok': True, 'msg': 'Mensagem de fim sendo disparada...'})

# ── Inicialização ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    db.init_db()
    scheduler.iniciar()
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', 5000))
    print(f'🙏 Culto App rodando em http://{host}:{port}')
    app.run(host=host, port=port, debug=False)
