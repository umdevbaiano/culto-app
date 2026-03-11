import database as db


class TestCadastroMembros:
    def test_cadastrar_sucesso(self):
        ok, msg = db.cadastrar_membro('João Silva', '73999990001')
        assert ok is True
        assert 'sucesso' in msg.lower()

    def test_cadastrar_duplicado(self):
        db.cadastrar_membro('João Silva', '73999990001')
        ok, msg = db.cadastrar_membro('João Outro', '73999990001')
        assert ok is False
        assert 'cadastrado' in msg.lower()

    def test_cadastrar_com_nascimento(self):
        ok, _ = db.cadastrar_membro('Maria', '73999990002', '2000-01-15')
        assert ok is True
        membro = db.buscar_membro_por_telefone('73999990002')
        assert membro['nascimento'] == '2000-01-15'

    def test_listar_membros(self):
        db.cadastrar_membro('Ana', '73999990003')
        db.cadastrar_membro('Bruno', '73999990004')
        membros = db.listar_membros()
        assert len(membros) == 2
        assert membros[0]['nome'] == 'Ana'  # ORDER BY nome

    def test_buscar_por_telefone(self):
        db.cadastrar_membro('Carlos', '73999990005')
        m = db.buscar_membro_por_telefone('73999990005')
        assert m is not None
        assert m['nome'] == 'Carlos'

    def test_buscar_inexistente(self):
        m = db.buscar_membro_por_telefone('00000000000')
        assert m is None


class TestRespostas:
    def test_registrar_resposta(self):
        db.cadastrar_membro('João', '73999990001')
        membro = db.buscar_membro_por_telefone('73999990001')
        ok = db.registrar_resposta(membro['id'], '2025-01-01', 'sim')
        assert ok is True

    def test_respostas_do_dia(self):
        db.cadastrar_membro('João', '73999990001')
        db.cadastrar_membro('Maria', '73999990002')
        m1 = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m1['id'], '2025-01-01', 'sim')

        respostas = db.respostas_do_dia('2025-01-01')
        assert len(respostas) == 2  # 2 membros
        confirmados = [r for r in respostas if r['resposta'] == 'sim']
        assert len(confirmados) == 1

    def test_substituir_resposta(self):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], '2025-01-01', 'nao')
        db.registrar_resposta(m['id'], '2025-01-01', 'sim')  # troca de ideia
        respostas = db.respostas_do_dia('2025-01-01')
        assert respostas[0]['resposta'] == 'sim'


class TestHistorico:
    def test_historico_por_periodo(self):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], '2025-01-01', 'sim')
        db.registrar_resposta(m['id'], '2025-01-02', 'nao')

        resultado = db.historico_por_periodo('2025-01-01', '2025-01-31')
        assert '2025-01-01' in resultado
        assert '2025-01-02' in resultado
        assert resultado['2025-01-01'][0]['resposta'] == 'sim'

    def test_historico_periodo_vazio(self):
        resultado = db.historico_por_periodo('2099-01-01', '2099-12-31')
        assert resultado == {}

    def test_historico_por_membro(self):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], '2025-01-01', 'sim')
        db.registrar_resposta(m['id'], '2025-01-02', 'nao')

        hist = db.historico_por_membro(m['id'])
        assert len(hist) == 2
        assert hist[0]['data'] == '2025-01-02'  # DESC


class TestEstatisticas:
    def test_estatisticas_gerais_vazio(self):
        stats = db.estatisticas_gerais()
        assert stats['total_cultos'] == 0
        assert stats['total_membros'] == 0
        assert stats['media_presenca'] == 0

    def test_estatisticas_gerais_com_dados(self):
        db.cadastrar_membro('João', '73999990001')
        db.cadastrar_membro('Maria', '73999990002')
        m1 = db.buscar_membro_por_telefone('73999990001')
        m2 = db.buscar_membro_por_telefone('73999990002')

        db.registrar_resposta(m1['id'], '2025-01-01', 'sim')
        db.registrar_resposta(m2['id'], '2025-01-01', 'sim')
        db.registrar_resposta(m1['id'], '2025-01-02', 'sim')
        db.registrar_resposta(m2['id'], '2025-01-02', 'nao')

        stats = db.estatisticas_gerais()
        assert stats['total_cultos'] == 2
        assert stats['total_membros'] == 2
        assert stats['media_presenca'] == 1.5  # 3 sim / 2 cultos
        assert len(stats['ranking']) == 2
        assert stats['ranking'][0]['nome'] == 'João'  # mais presenças

    def test_estatisticas_membro(self):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], '2025-01-01', 'sim')
        db.registrar_resposta(m['id'], '2025-01-02', 'nao')
        db.registrar_resposta(m['id'], '2025-01-03', 'sim')

        stats = db.estatisticas_membro(m['id'])
        assert stats is not None
        assert stats['total_cultos'] == 3
        assert stats['presencas'] == 2
        assert stats['percentual'] == 66.7

    def test_estatisticas_membro_inexistente(self):
        assert db.estatisticas_membro(9999) is None


class TestConfig:
    def test_defaults(self):
        config = db.get_config()
        assert config['horario_pre_culto'] == '19:00'
        assert config['horario_fim_culto'] == '21:00'
        assert config['dias_culto'] == '2,5,6'

    def test_alterar_config(self):
        db.set_config('horario_pre_culto', '18:00')
        config = db.get_config()
        assert config['horario_pre_culto'] == '18:00'
