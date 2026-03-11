import threading
import time
from datetime import datetime, date

# Importações locais
import database as db
import whatsapp as wa

_lock = threading.Lock()
_ultimo_pre = None
_ultimo_fim = None

def _hoje():
    return date.today().isoformat()

def _hora_atual():
    return datetime.now().strftime('%H:%M')

def _dia_semana_atual():
    """0=segunda ... 6=domingo"""
    return datetime.now().weekday()

def _dias_habilitados(config):
    """Retorna set de dias da semana habilitados."""
    raw = config.get('dias_culto', '3,5,6')
    return set(int(d.strip()) for d in raw.split(',') if d.strip())

# ── Disparos ──────────────────────────────────────────────────────────────────

def disparar_pre_culto():
    print(f'[SCHED] ⏰ Disparando pré-culto — {datetime.now()}')
    config = db.get_config()
    membros = db.listar_membros()
    hoje = _hoje()

    for m in membros:
        nome = m['nome'].split()[0]  # primeiro nome
        msg_template = config.get('msg_pre_culto', 'Olá, {nome}! Vai participar do culto hoje?')

        try:
            wa.enviar_lista_interativa(
                m['telefone'],
                titulo='🙏 Culto de hoje',
                corpo=msg_template.replace('{nome}', nome),
                botoes=[
                    {'id': f'sim_{m["id"]}_{hoje}', 'title': 'Estarei lá! 🙌'},
                    {'id': f'nao_{m["id"]}_{hoje}', 'title': 'Não vou poder ir 😔'},
                ]
            )
        except Exception as e:
            print(f'[SCHED] Erro ao enviar para {m["nome"]}: {e}')

        time.sleep(1)  # evita flood

def disparar_fim_culto():
    print(f'[SCHED] ⏰ Disparando fim do culto — {datetime.now()}')
    config = db.get_config()
    hoje = _hoje()
    membros_dia = db.respostas_do_dia(hoje)
    youtube = config.get('youtube_channel', '')

    for m in membros_dia:
        nome = m['nome'].split()[0]
        resposta = m.get('resposta')

        if resposta == 'sim':
            msg = config.get('msg_ate_amanha', 'Até amanhã, {nome}! 🙏').replace('{nome}', nome)
        else:
            msg = config.get('msg_ausente_fim', 'Sentimos sua falta, {nome}! 💙').replace('{nome}', nome)

        wa.enviar_mensagem(m['telefone'], msg)
        time.sleep(1)

# ── Loop principal ────────────────────────────────────────────────────────────

def _loop():
    global _ultimo_pre, _ultimo_fim
    print('[SCHED] 🚀 Agendador iniciado')

    while True:
        try:
            config = db.get_config()
            hora = _hora_atual()
            dia = _dia_semana_atual()
            dias_ok = _dias_habilitados(config)

            if dia in dias_ok:
                horario_pre = config.get('horario_pre_culto', '19:00')
                horario_fim = config.get('horario_fim_culto', '21:00')
                hoje = _hoje()

                # Pré-culto
                if hora == horario_pre and _ultimo_pre != hoje:
                    with _lock:
                        if _ultimo_pre != hoje:
                            _ultimo_pre = hoje
                            threading.Thread(target=disparar_pre_culto, daemon=True).start()

                # Fim do culto
                if hora == horario_fim and _ultimo_fim != hoje:
                    with _lock:
                        if _ultimo_fim != hoje:
                            _ultimo_fim = hoje
                            threading.Thread(target=disparar_fim_culto, daemon=True).start()

        except Exception as e:
            print(f'[SCHED] ❌ Erro no loop: {e}')

        time.sleep(30)  # verifica a cada 30 segundos

def iniciar():
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
