import json
import database as db


class TestCadastroAPI:
    def test_cadastro_sucesso(self, app_client):
        resp = app_client.post('/api/cadastro', json={
            'nome': 'João Silva',
            'telefone': '73999990001'
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['ok'] is True

    def test_cadastro_sem_nome(self, app_client):
        resp = app_client.post('/api/cadastro', json={
            'nome': '',
            'telefone': '73999990001'
        })
        assert resp.status_code == 400

    def test_cadastro_duplicado(self, app_client):
        app_client.post('/api/cadastro', json={
            'nome': 'João', 'telefone': '73999990001'
        })
        resp = app_client.post('/api/cadastro', json={
            'nome': 'Maria', 'telefone': '73999990001'
        })
        data = resp.get_json()
        assert data['ok'] is False


class TestWebhookAPI:
    def _webhook_msg(self, client, telefone, texto):
        return client.post('/api/webhook', json={
            'event': 'messages.upsert',
            'data': {
                'key': {
                    'fromMe': False,
                    'remoteJid': f'{telefone}@s.whatsapp.net'
                },
                'message': {'conversation': texto}
            }
        })

    def test_webhook_confirma(self, app_client):
        db.cadastrar_membro('João', '73999990001')
        resp = self._webhook_msg(app_client, '73999990001', 'sim')
        assert resp.status_code == 200

    def test_webhook_nega(self, app_client):
        db.cadastrar_membro('João', '73999990001')
        resp = self._webhook_msg(app_client, '73999990001', 'não')
        assert resp.status_code == 200

    def test_webhook_ignora_fromMe(self, app_client):
        resp = app_client.post('/api/webhook', json={
            'event': 'messages.upsert',
            'data': {
                'key': {'fromMe': True, 'remoteJid': '73999990001@s.whatsapp.net'},
                'message': {'conversation': 'sim'}
            }
        })
        assert resp.status_code == 200

    def test_webhook_evento_invalido(self, app_client):
        resp = app_client.post('/api/webhook', json={'event': 'outro'})
        assert resp.status_code == 200


class TestPainelAPI:
    def test_painel_vazio(self, app_client):
        resp = app_client.get('/api/painel')
        data = resp.get_json()
        assert 'confirmados' in data
        assert 'ausentes' in data
        assert 'aguardando' in data


class TestMembrosAPI:
    def test_listar_membros(self, app_client):
        db.cadastrar_membro('Ana', '73999990003')
        resp = app_client.get('/api/membros')
        data = resp.get_json()
        assert len(data) == 1

    def test_adicionar_membro(self, app_client):
        resp = app_client.post('/api/membros', json={
            'nome': 'Bruno', 'telefone': '73999990004'
        })
        data = resp.get_json()
        assert data['ok'] is True


class TestConfigAPI:
    def test_get_config(self, app_client):
        resp = app_client.get('/api/config')
        data = resp.get_json()
        assert 'horario_pre_culto' in data

    def test_set_config(self, app_client):
        resp = app_client.post('/api/config', json={
            'horario_pre_culto': '18:30'
        })
        assert resp.get_json()['ok'] is True

        resp = app_client.get('/api/config')
        assert resp.get_json()['horario_pre_culto'] == '18:30'


class TestHistoricoAPI:
    def test_historico_padrao(self, app_client):
        resp = app_client.get('/api/historico')
        data = resp.get_json()
        assert 'inicio' in data
        assert 'fim' in data
        assert 'dias' in data

    def test_historico_com_dados(self, app_client):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], '2025-06-15', 'sim')

        resp = app_client.get('/api/historico?inicio=2025-06-01&fim=2025-06-30')
        data = resp.get_json()
        assert '2025-06-15' in data['dias']

    def test_historico_membro(self, app_client):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], '2025-06-15', 'sim')

        resp = app_client.get(f'/api/historico/{m["id"]}')
        data = resp.get_json()
        assert len(data) == 1


class TestEstatisticasAPI:
    def test_estatisticas_gerais(self, app_client):
        resp = app_client.get('/api/estatisticas')
        data = resp.get_json()
        assert 'total_cultos' in data
        assert 'ranking' in data

    def test_estatisticas_membro(self, app_client):
        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        resp = app_client.get(f'/api/estatisticas/{m["id"]}')
        data = resp.get_json()
        assert 'presencas' in data

    def test_estatisticas_membro_404(self, app_client):
        resp = app_client.get('/api/estatisticas/9999')
        assert resp.status_code == 404


class TestRateLimiting:
    def test_rate_limit_cadastro(self, app_client):
        # Limite de 5 cadastros por minuto
        for i in range(5):
            resp = app_client.post('/api/cadastro', json={
                'nome': f'User {i}', 'telefone': f'7399999{i:04d}'
            })
            assert resp.status_code == 200

        # 6o deve ser bloqueado
        resp = app_client.post('/api/cadastro', json={
            'nome': 'Excesso', 'telefone': '73999999999'
        })
        assert resp.status_code == 429

    def test_rate_limit_disparo(self, app_client):
        resp1 = app_client.post('/api/disparar/pre')
        resp2 = app_client.post('/api/disparar/pre')
        assert resp1.status_code == 200
        assert resp2.status_code == 200

        resp3 = app_client.post('/api/disparar/pre')
        assert resp3.status_code == 429


class TestDisparosAPI:
    def test_disparar_pre(self, app_client):
        resp = app_client.post('/api/disparar/pre')
        data = resp.get_json()
        assert data['ok'] is True

    def test_disparar_fim(self, app_client):
        resp = app_client.post('/api/disparar/fim')
        data = resp.get_json()
        assert data['ok'] is True
