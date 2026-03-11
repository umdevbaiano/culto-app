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
    Envia uma Enquete (Poll) interativa pelo WhatsApp,
    usando os botões como opções clicáveis.
    """
    numero = _formatar_numero(telefone)
    url = f'{EVOLUTION_URL}/message/sendPoll/{EVOLUTION_INSTANCE}'
    
    # Extrai só os títulos para criar as opções da enquete
    opcoes = [b['title'] for b in botoes]
    
    payload = {
        'number': numero,
        'options': {
            'delay': 1200,
            'presence': 'composing'
        },
        'pollMessage': {
            'name': f'{titulo}\n\n{corpo}',
            'options': opcoes,
            'selectableCount': 1
        }
    }
    
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=10)
        resp.raise_for_status()
        print(f'[WA] ✅ Enquete enviada para {numero}', flush=True)
        return True
    except Exception as e:
        print(f'[WA] ❌ Erro ao enviar enquete para {numero}: {e}', flush=True)
        if hasattr(e, 'response') and e.response is not None:
            print(f'[WA] Detalhes do erro: {e.response.text}', flush=True)
        
        # Fallback de sobrevivência (Texto simples)
        fallback = "\n".join([f"*{i+1}* - {b['title']}" for i, b in enumerate(botoes)])
        return enviar_mensagem(telefone, f'{titulo}\n\n{corpo}\n\nResponda:\n{fallback}')

def enviar_midia(telefone, mensagem, base64_media, media_type='image', file_name='arquivo.png'):
    """
    Envia mídia (imagem, pdf, etc) via base64.
    media_type: 'image', 'document', 'audio', 'video'
    """
    numero = _formatar_numero(telefone)
    url = f'{EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCE}'
    
    payload = {
        'number': numero,
        'options': {
            'delay': 2000,
            'presence': 'composing'
        },
        'mediaMessage': {
            'mediatype': media_type,
            'fileName': file_name,
            'caption': mensagem,
            'media': base64_media
        }
    }
    
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=20)
        resp.raise_for_status()
        print(f'[WA] ✅ Mídia enviada para {numero}', flush=True)
        return True
    except Exception as e:
        print(f'[WA] ❌ Erro ao enviar mídia para {numero}: {e}', flush=True)
        if hasattr(e, 'response') and e.response is not None:
            print(f'[WA] Detalhes do erro: {e.response.text}', flush=True)
        return False
