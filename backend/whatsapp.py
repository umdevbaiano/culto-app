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
    
    # Payload no formato Evolution API v1.8.2
    payload = {
        'number': numero,
        'options': {
            'delay': 1200,
            'presence': 'composing'
        },
        'textMessage': {
            'text': mensagem
        }
    }
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        print(f'[WA] ✅ Mensagem enviada para {numero}', flush=True)
        return True
    except Exception as e:
        print(f'[WA] ❌ Erro ao enviar para {numero}: {e}', flush=True)
        if hasattr(e, 'response') and e.response is not None:
            print(f'[WA] Detalhes do erro: {e.response.text}', flush=True)
        return False

def enviar_lista_interativa(telefone, titulo, corpo, botoes):
    """
    Simula envio de lista interativa enviando um menu de texto simples,
    pois os botões nativos não são mais suportados na versão Baileys (QR Code).
    """
    numero = _formatar_numero(telefone)
    
    # Fallback obrigatório: envia texto simples com instruções
    print(f'[WA] ⚠️ Acionando fallback de botões para {numero}.', flush=True)
    
    # Removido o envio do sendButtons pois a API Baileys da v1.8.2 recusa.
    # Formatando a lista de botões como opções de texto
    opcoes_texto = "\n".join([f"*{i+1}* - {b['title']}" for i, b in enumerate(botoes)])
    msg_fallback = f'{titulo}\n\n{corpo}\n\nResponda:\n{opcoes_texto}'
    
    return enviar_mensagem(telefone, msg_fallback)
