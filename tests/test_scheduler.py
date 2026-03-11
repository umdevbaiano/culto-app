import database as db
import scheduler


class TestDiasHabilitados:
    def test_parse_dias(self):
        config = {'dias_culto': '2,5,6'}
        dias = scheduler._dias_habilitados(config)
        assert dias == {2, 5, 6}

    def test_parse_dias_com_espacos(self):
        config = {'dias_culto': ' 0 , 3 , 6 '}
        dias = scheduler._dias_habilitados(config)
        assert dias == {0, 3, 6}

    def test_parse_default(self):
        config = {}
        dias = scheduler._dias_habilitados(config)
        assert dias == {3, 5, 6}  # fallback padrão do scheduler


class TestDisparos:
    def test_disparar_pre_culto(self, monkeypatch):
        import whatsapp as wa
        mensagens = []
        monkeypatch.setattr(wa, 'enviar_lista_interativa',
                            lambda tel, titulo, corpo, botoes: mensagens.append(tel))

        db.cadastrar_membro('João', '73999990001')
        db.cadastrar_membro('Maria', '73999990002')

        scheduler.disparar_pre_culto()
        assert len(mensagens) == 2

    def test_disparar_fim_culto(self, monkeypatch):
        import whatsapp as wa
        mensagens = []
        monkeypatch.setattr(wa, 'enviar_mensagem',
                            lambda tel, msg: mensagens.append((tel, msg)))

        db.cadastrar_membro('João', '73999990001')
        m = db.buscar_membro_por_telefone('73999990001')
        db.registrar_resposta(m['id'], db.get_config and scheduler._hoje(), 'sim')

        scheduler.disparar_fim_culto()
        assert len(mensagens) >= 1
