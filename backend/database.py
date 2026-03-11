import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'culto.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Membros
    c.execute('''
        CREATE TABLE IF NOT EXISTS membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL UNIQUE,
            nascimento TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')

    # Respostas diárias
    c.execute('''
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membro_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            resposta TEXT NOT NULL,
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (membro_id) REFERENCES membros(id),
            UNIQUE(membro_id, data)
        )
    ''')

    # Configurações
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    ''')

    # Defaults de configuração
    defaults = {
        'horario_pre_culto': '19:00',
        'horario_fim_culto': '21:00',
        'dias_culto': '2,5,6',  # Qua=2, Sáb=5, Dom=6 (weekday: 0=Seg..6=Dom)
        'youtube_channel': 'https://youtube.com/@seucanal',
        'msg_pre_culto': 'Olá, {nome}! 🙏 Vai participar do culto hoje?',
        'msg_boas_vindas': 'Bem-vindo ao culto, {nome}! 🙏 Que Deus abençoe sua presença!',
        'msg_ausente_pre': 'Sentimos sua falta, {nome}! 😔 Assista à nossa live: {youtube}',
        'msg_ate_amanha': 'Até amanhã, {nome}! 🙏 Foi uma bênção ter você conosco hoje!',
        'msg_ausente_fim': 'Sentimos sua falta hoje, {nome}! 💙 Te esperamos no próximo culto. Deus te abençoe!',
    }

    for chave, valor in defaults.items():
        c.execute('INSERT OR IGNORE INTO config (chave, valor) VALUES (?, ?)', (chave, valor))

    conn.commit()
    conn.close()

# ── Membros ───────────────────────────────────────────────────────────────────

def cadastrar_membro(nome, telefone, nascimento=None):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO membros (nome, telefone, nascimento) VALUES (?, ?, ?)',
            (nome, telefone, nascimento)
        )
        conn.commit()
        return True, 'Cadastro realizado com sucesso!'
    except sqlite3.IntegrityError:
        return False, 'Número já cadastrado.'
    finally:
        conn.close()

def listar_membros(apenas_ativos=True):
    conn = get_conn()
    q = 'SELECT * FROM membros'
    if apenas_ativos:
        q += ' WHERE ativo = 1'
    q += ' ORDER BY nome'
    rows = conn.execute(q).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def buscar_membro_por_telefone(telefone):
    conn = get_conn()
    row = conn.execute('SELECT * FROM membros WHERE telefone = ?', (telefone,)).fetchone()
    conn.close()
    return dict(row) if row else None

def atualizar_membro(membro_id, nome, telefone, nascimento, ativo):
    conn = get_conn()
    try:
        # Se for atualizar o telefone, vai falhar por UNIQUE se já existir em outro ID
        conn.execute('''
            UPDATE membros 
            SET nome = ?, telefone = ?, nascimento = ?, ativo = ? 
            WHERE id = ?
        ''', (nome, telefone, nascimento, 1 if ativo else 0, membro_id))
        conn.commit()
        return True, 'Membro atualizado com sucesso!'
    except sqlite3.IntegrityError:
        return False, 'O novo telefone já pertence a outro membro.'
    finally:
        conn.close()

def deletar_membro(membro_id):
    conn = get_conn()
    try:
        # Excluir histórico de respostas para não deixar órfãos, 
        # caso não esteja usando ON DELETE CASCADE na tabela:
        conn.execute('DELETE FROM respostas WHERE membro_id = ?', (membro_id,))
        # Excluir o membro propriamente dito
        conn.execute('DELETE FROM membros WHERE id = ?', (membro_id,))
        conn.commit()
        return True, 'Membro e seu histórico foram removidos com sucesso!'
    except Exception as e:
        return False, f'Erro ao deletar: {e}'
    finally:
        conn.close()

# ── Respostas ─────────────────────────────────────────────────────────────────

def registrar_resposta(membro_id, data, resposta):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT OR REPLACE INTO respostas (membro_id, data, resposta) VALUES (?, ?, ?)',
            (membro_id, data, resposta)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def respostas_do_dia(data):
    conn = get_conn()
    rows = conn.execute('''
        SELECT m.id, m.nome, m.telefone, r.resposta
        FROM membros m
        LEFT JOIN respostas r ON m.id = r.membro_id AND r.data = ?
        WHERE m.ativo = 1
        ORDER BY m.nome
    ''', (data,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Histórico ─────────────────────────────────────────────────────────────────

def historico_por_periodo(data_inicio, data_fim):
    """Retorna respostas agrupadas por data dentro de um período."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT r.data, m.id as membro_id, m.nome, m.telefone, r.resposta
        FROM respostas r
        JOIN membros m ON m.id = r.membro_id
        WHERE r.data BETWEEN ? AND ?
        ORDER BY r.data DESC, m.nome
    ''', (data_inicio, data_fim)).fetchall()
    conn.close()

    # Agrupa por data
    resultado = {}
    for r in rows:
        d = dict(r)
        data = d.pop('data')
        if data not in resultado:
            resultado[data] = []
        resultado[data].append(d)
    return resultado

def historico_por_membro(membro_id):
    """Retorna o histórico de presença de um membro específico."""
    conn = get_conn()
    rows = conn.execute('''
        SELECT r.data, r.resposta, r.criado_em
        FROM respostas r
        WHERE r.membro_id = ?
        ORDER BY r.data DESC
    ''', (membro_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Estatísticas ──────────────────────────────────────────────────────────────

def estatisticas_gerais():
    """Retorna estatísticas gerais da igreja."""
    conn = get_conn()

    # Total de cultos realizados (dias distintos com respostas)
    total_cultos = conn.execute(
        'SELECT COUNT(DISTINCT data) FROM respostas'
    ).fetchone()[0] or 0

    # Total de membros ativos
    total_membros = conn.execute(
        'SELECT COUNT(*) FROM membros WHERE ativo = 1'
    ).fetchone()[0] or 0

    # Média de presença por culto
    media_presenca = 0
    if total_cultos > 0:
        total_sim = conn.execute(
            "SELECT COUNT(*) FROM respostas WHERE resposta = 'sim'"
        ).fetchone()[0] or 0
        media_presenca = round(total_sim / total_cultos, 1)

    # Ranking de frequência (top 10)
    ranking = conn.execute('''
        SELECT m.id, m.nome, m.telefone,
               COUNT(CASE WHEN r.resposta = 'sim' THEN 1 END) as presencas,
               COUNT(r.id) as total_respostas
        FROM membros m
        LEFT JOIN respostas r ON m.id = r.membro_id
        WHERE m.ativo = 1
        GROUP BY m.id
        ORDER BY presencas DESC
        LIMIT 10
    ''').fetchall()

    # Presença por dia (últimos 30 dias com dados)
    presenca_por_dia = conn.execute('''
        SELECT data,
               COUNT(CASE WHEN resposta = 'sim' THEN 1 END) as presentes,
               COUNT(CASE WHEN resposta = 'nao' THEN 1 END) as ausentes
        FROM respostas
        GROUP BY data
        ORDER BY data DESC
        LIMIT 30
    ''').fetchall()

    conn.close()

    return {
        'total_cultos': total_cultos,
        'total_membros': total_membros,
        'media_presenca': media_presenca,
        'ranking': [dict(r) for r in ranking],
        'presenca_por_dia': [dict(r) for r in presenca_por_dia],
    }

def estatisticas_membro(membro_id):
    """Retorna estatísticas de um membro específico."""
    conn = get_conn()

    membro = conn.execute(
        'SELECT * FROM membros WHERE id = ?', (membro_id,)
    ).fetchone()
    if not membro:
        conn.close()
        return None

    total = conn.execute(
        'SELECT COUNT(*) FROM respostas WHERE membro_id = ?', (membro_id,)
    ).fetchone()[0] or 0

    presencas = conn.execute(
        "SELECT COUNT(*) FROM respostas WHERE membro_id = ? AND resposta = 'sim'",
        (membro_id,)
    ).fetchone()[0] or 0

    percentual = round((presencas / total * 100), 1) if total > 0 else 0

    # Últimas 10 respostas
    ultimas = conn.execute('''
        SELECT data, resposta FROM respostas
        WHERE membro_id = ?
        ORDER BY data DESC LIMIT 10
    ''', (membro_id,)).fetchall()

    conn.close()

    return {
        'membro': dict(membro),
        'total_cultos': total,
        'presencas': presencas,
        'percentual': percentual,
        'ultimas': [dict(r) for r in ultimas],
    }

# ── Config ────────────────────────────────────────────────────────────────────

def get_config():
    conn = get_conn()
    rows = conn.execute('SELECT chave, valor FROM config').fetchall()
    conn.close()
    return {r['chave']: r['valor'] for r in rows}

def set_config(chave, valor):
    conn = get_conn()
    conn.execute('INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)', (chave, valor))
    conn.commit()
    conn.close()
