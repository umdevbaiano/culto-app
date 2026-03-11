# Como Fazer o Deploy do Culto App em VPS

Este guia passo a passo ensina como subir o **Culto App** e seu banco de dados nativo num servidor limpo (como Ubuntu Server ou Debian) hospedado numa VPS (AWS, DigitalOcean, Hetzner, Hostinger, etc).

---

## 1. Primeiros Passos no Servidor
Com o servidor criado e acessado por SSH (ex: `ssh root@SEU-IP`), atualize os pacotes e instale git e curl:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git curl zip unzip -y
```

## 2. Instalando o Docker e o Git
Baixe e instale a engine oficial do Docker, necessária para rodar todos os serviços do sistema:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

## 3. Clonando o Projeto
```bash
git clone https://github.com/SEU_USUARIO/culto-app.git
cd culto-app
```
*(Se o repositório for privado, você precisará gerar um Personal Access Token no GitHub ou se autenticar no terminal)*

## 4. Configurando Variáveis de Arquivo (.env)
Crie o arquivo que vai guardar as credenciais secretas e as configurações do banco de dados na raiz da pasta do app:
```bash
cp sample.env .env
nano .env
```
Copie e edite as informações. Certifique-se de preencher `ADMIN_USER` e `ADMIN_PASS` com credenciais fortes, pois este app ficará aberto na internet:
```ini
ADMIN_USER=pastor
ADMIN_PASS=minhasenhasecreta

# ... resto do env (EVOLUTION_API, POSTGRES do Baileys, etc) ...
```

## 5. Rodando o Sistema
Uma vez logado dentro da pasta `/culto-app` contendo o arquivo `docker-compose.yml` e o `.env`, bastará executar:
```bash
docker compose up -d --build
```
Isso vai construir a imagem do Python (`app`) pelo `Dockerfile`, e baixar e inicializar o `Evolution API` e seus bancos dependentes (`PostgreSQL` e `Redis`).

### Parando os Serviços
Para parar ou reiniciar tudo de forma coesa sem deletar dados:
```bash
docker compose stop   # apenas para, sem descartar logs ou redes
docker compose down   # desliga os contêineres mas os "volumes" (dados) continuam
```

## 6. Acessando e Autenticando
Abra no navegador em qualquer computador/celular o endereço:
**`http://IP_DO_SEU_SERVIDOR:5000/admin`**

- O navegador solicitará uma tela padrão de Usuário e Senha. Digite os do seu arquivo `.env` e clique em Fazer login.
- Lembre-se que o banco de dados nativo (Culto) persistirá sozinho na pasta `backups/` e no próprio `culto.db` atrelado no Host da VPS.

*(Para produção real com HTTPS seguro e proteção de interceptação de rede, recomendamos instalar um Proxy Reverso como Nginx Proxy Manager ou Cloudflare Tunnels mapeando para a porta `5000`)*
