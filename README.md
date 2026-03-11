# 🙏 Sistema de Gestão de Culto

Automação completa de comunicação com membros via WhatsApp, com painel administrativo, histórico de presenças e estatísticas.

---

## Funcionalidades

- ✅ **Cadastro de membros** via formulário web (QR Code)
- 📨 **Disparo automático** de mensagens pré-culto nos dias/horários configurados
- 🙏 **Mensagens de fim de culto** personalizadas (presentes vs ausentes)
- 🔔 **Webhook** para receber respostas dos membros em tempo real
- 📅 **Histórico de presenças** — consulta por período com detalhes por dia
- 📊 **Estatísticas** — ranking de frequência, média por culto, gráfico de presença
- ⚙️ **Configuração pelo admin** — horários, dias, mensagens customizáveis
- 🛡️ **Rate limiting** em todas as APIs
- 🐳 **Docker** — sobe tudo com um comando
- 🧪 **45 testes automatizados** com CI/CD via GitHub Actions

---

## Pré-requisitos

- Docker e Docker Compose instalados
- Chip de celular secundário para conectar ao WhatsApp

---

## Instalação rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/culto-app.git
cd culto-app

# 2. Configure o .env
cp .env.example .env
# Edite o .env com seus dados (YouTube, IP, etc.)

# 3. Suba tudo
docker compose up -d --build

# Ou no Windows, dê duplo clique no:
start.bat
```

---

## Configuração

### Variáveis de ambiente (.env)

```env
# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://evolution:8080
EVOLUTION_API_KEY=sua_chave_aqui
EVOLUTION_INSTANCE=igreja

# App
APP_HOST=0.0.0.0
APP_PORT=5000
APP_URL=http://SEU_IP:5000

# Igreja
YOUTUBE_CHANNEL=https://youtube.com/@seucanal
```

### Configurar webhook na Evolution API

Após escanear o QR Code na Evolution, configure o webhook:

```
URL: http://app:5000/api/webhook
Eventos: MESSAGES_UPSERT
```

---

## Endereços

| Endereço | Descrição |
|---|---|
| http://localhost:5000 | Formulário de cadastro |
| http://localhost:5000/admin | Painel administrativo |
| http://localhost:8080/manager | Painel da Evolution API |

---

## Fluxo de comunicação

```
PRÉ-CULTO (horário configurável)
Sistema dispara → "Vai vir hoje?"
    ↓ Sim                  ↓ Não
"Bem-vindo ao culto!"  "Live: youtube.com/@canal"

FIM DO CULTO (horário configurável)
    ↓ Quem confirmou       ↓ Quem não foi
"Até amanhã! 🙏"       "Sentimos sua falta!"
```

---

## Painel Admin — 5 abas

| Aba | Funcionalidade |
|-----|---------------|
| **Culto de Hoje** | Stats em tempo real + botões de disparo manual |
| **Membros** | Cadastro manual + lista completa |
| **Histórico** | Filtro por datas + presença detalhada por dia |
| **Estatísticas** | Ranking, média, gráfico de presença ao longo do tempo |
| **Configurações** | Horários, dias da semana, mensagens, YouTube |

---

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/cadastro` | Cadastrar membro |
| `POST` | `/api/webhook` | Webhook da Evolution API |
| `GET` | `/api/painel` | Dados do culto de hoje |
| `GET/POST` | `/api/membros` | Listar/adicionar membros |
| `GET/POST` | `/api/config` | Ler/salvar configurações |
| `GET` | `/api/historico` | Histórico por período |
| `GET` | `/api/historico/<id>` | Histórico de um membro |
| `GET` | `/api/estatisticas` | Estatísticas gerais |
| `GET` | `/api/estatisticas/<id>` | Estatísticas de um membro |
| `POST` | `/api/disparar/pre` | Disparo manual pré-culto |
| `POST` | `/api/disparar/fim` | Disparo manual fim de culto |

---

## Testes

```bash
python -m pytest tests/ -v
```

45 testes cobrindo: database, API, scheduler, rate limiting, histórico e estatísticas.

---

## Estrutura

```
culto-app/
├── backend/
│   ├── app.py          # Flask + rotas API + rate limiter
│   ├── database.py     # SQLite (membros, respostas, config, histórico, stats)
│   ├── whatsapp.py     # Integração Evolution API
│   └── scheduler.py    # Agendador automático de mensagens
├── frontend/
│   ├── form.html       # Formulário de cadastro
│   └── admin.html      # Painel admin (5 abas)
├── tests/
│   ├── conftest.py     # Fixtures (temp DB + mock WhatsApp)
│   ├── test_database.py
│   ├── test_api.py
│   └── test_scheduler.py
├── .github/workflows/
│   └── ci.yml          # GitHub Actions (pytest em push/PR)
├── Dockerfile
├── docker-compose.yml  # App + Evolution API
├── start.bat           # Iniciar tudo no Windows
├── .env.example
├── requirements.txt
└── README.md
```

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11 / Flask |
| Banco de Dados | SQLite |
| Frontend | HTML + CSS + JavaScript (vanilla) |
| WhatsApp | Evolution API |
| Deploy | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Testes | pytest |
