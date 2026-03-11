import os
import requests

EVOLUTION_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
EVOLUTION_KEY = os.getenv('EVOLUTION_API_KEY', '')
EVOLUTION_INSTANCE = os.getenv('EVOLUTION_INSTANCE', 'igreja')

def _headers():
    return {
        'apikey': EVOLUTION_KEY,
        'Content-Type': 'application/json'
    }

def _formatar_numero(telefone):
    """Remove tudo que não for dígito e garante DDI 55."""
    numero = ''.join(filter(str.isdigit, telefone))
    if not numero.startswith('55'):
        numero = '55' + numero
    return numero

def enviar_mensagem(telefone, mensagem):
    """Envia mensagem de texto via Evolution API."""
    numero = _formatar_numero(telefone)
    url = f'{EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCE}'
    payload = {
        'number': numero,
        'text': mensagem
    }
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        print(f'[WA] ✅ Mensagem enviada para {numero}')
        return True
    except Exception as e:
        print(f'[WA] ❌ Erro ao enviar para {numero}: {e}')
        return False

def enviar_lista_interativa(telefone, titulo, corpo, botoes):
    """
    Envia mensagem com botões de resposta rápida.
    botoes = [{'id': 'sim', 'title': 'Estarei lá! 🙌'}, ...]
    """
    numero = _formatar_numero(telefone)
    url = f'{EVOLUTION_URL}/message/sendButtons/{EVOLUTION_INSTANCE}'
    payload = {
        'number': numero,
        'title': titulo,
        'description': corpo,
        'buttons': [{'buttonId': b['id'], 'buttonText': {'displayText': b['title']}} for b in botoes],
        'footerText': 'Igreja'
    }
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        print(f'[WA] ✅ Botões enviados para {numero}')
        return True
    except Exception as e:
        # Fallback: envia texto simples com instruções
        print(f'[WA] ⚠️ Botões não suportados para {numero}, enviando texto.')
        msg_fallback = f'{corpo}\n\nResponda:\n*1* - Estarei lá! 🙌\n*2* - Não vou poder ir 😔'
        return enviar_mensagem(telefone, msg_fallback)
