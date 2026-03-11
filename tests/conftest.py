import os
import sys
import tempfile
import pytest

# Garante que o backend está no path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import database as db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Usa um banco de dados temporário para cada teste."""
    db_path = str(tmp_path / 'test_culto.db')
    monkeypatch.setattr(db, 'DB_PATH', db_path)
    db.init_db()
    yield db_path


@pytest.fixture
def app_client(monkeypatch):
    """Flask test client com WhatsApp mockado."""
    import whatsapp as wa
    import app as flask_app

    # Mock do WhatsApp — não envia mensagens de verdade
    monkeypatch.setattr(wa, 'enviar_mensagem', lambda tel, msg: True)
    monkeypatch.setattr(wa, 'enviar_lista_interativa', lambda tel, titulo, corpo, botoes: True)

    flask_app.app.config['TESTING'] = True

    # Limpa o rate limiter entre testes
    flask_app._rate_store.clear()

    with flask_app.app.test_client() as client:
        yield client
