# Folga System

Sistema web Flask para gestao interna de folgas, justificativas, TRE, banco de horas, relatorios e cadastros de servidores da unidade escolar.

O projeto e usado como uma "Central da Unidade": servidores fazem solicitações e acompanham seu historico, enquanto administradores aprovam usuarios, deferem/indeferem registros, lancam saldos, gerenciam eventos, emitem relatorios e publicam avisos de atualizacao.

> **Atenção:** este projeto esta rodando em produção e o banco configurado/esperado em deploy e um banco de produção. Trate comandos de banco, migrations, scripts de sincronizacao, backups/restores e qualquer alteração de dados como operação sensível. Faça backup antes de mudanças estruturais e nunca rode comandos destrutivos sem confirmação explícita.

## Sumario

- [Visao geral](#visao-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Requisitos](#requisitos)
- [Configuracao local](#configuracao-local)
- [Variaveis de ambiente](#variaveis-de-ambiente)
- [Banco de dados e migracoes](#banco-de-dados-e-migracoes)
- [Como executar](#como-executar)
- [Docker](#docker)
- [Deploy no Render](#deploy-no-render)
- [Uploads e arquivos persistentes](#uploads-e-arquivos-persistentes)
- [Relatorios e PDFs](#relatorios-e-pdfs)
- [Rotas principais](#rotas-principais)
- [Backup](#backup)
- [Seguranca e pontos de atencao](#seguranca-e-pontos-de-atencao)
- [Manutencao](#manutencao)

## Visao geral

O sistema centraliza fluxos administrativos ligados a frequencia e afastamentos:

- cadastro, login, aprovacao e ativacao de usuarios;
- aceite obrigatorio de termo de uso vigente;
- agendamento de folgas por motivo;
- controle de Licenca Medica por periodo;
- registro e deferimento de Banco de Horas;
- envio, validacao e consumo de TRE;
- relato de esquecimento de ponto;
- calendario de eventos da unidade;
- relatorios de ponto, horas extras e prontuario do servidor;
- envio de comunicacoes por e-mail e BotBot/WhatsApp;
- patch notes para administradores.

O entrypoint principal e `app.py`. O projeto ainda possui `app-oficial.py`, que parece ser uma copia/snapshot legado do aplicativo, mas o Dockerfile, Procfile e comandos de execucao apontam para `app:app`.

## Funcionalidades

### Usuarios e autenticacao

- Login com Flask-Login.
- Registro publico de usuario.
- Aprovacao/rejeicao de usuarios pendentes por administrador.
- Bloqueio/inativacao de usuario sem remocao fisica.
- Recuperacao de senha por e-mail com token temporario.
- Alteracao de e-mail com confirmacao por token.
- Perfil com dados obrigatorios: celular, nascimento, CPF, RG e cargo.
- Aceite de termo de uso por versao (`TERMO_VERSION`).

### Agendamentos e folgas

Motivos conhecidos:

| Codigo | Significado |
| --- | --- |
| `AB` | Abonada |
| `BH` | Banco de Horas usufruido |
| `TRE` | TRE |
| `LM` | Licenca Medica |
| `DS` | Doacao de Sangue |
| `FS` | Falta Simples |
| `DL` | Dispensa Legal |

Regras importantes implementadas no backend:

- `AB`: limite de 1 por mes e 6 deferidas por ano.
- `BH`: valida saldo em minutos antes de permitir consumo.
- `TRE`: valida saldo disponivel antes de permitir agendamento.
- `LM`: quando existe periodo, cria um registro por dia com o mesmo `lote_id`.
- Substituicao pode ser informada pelo usuario ou pelo administrador.
- Cada agendamento pode gerar protocolo PDF.

### Banco de horas

- Servidor cadastra horas realizadas.
- Administrador pode inserir creditos manualmente.
- Fluxo de deferimento/indeferimento.
- Saldo do usuario e armazenado em minutos em `User.banco_horas`.
- O consumo de Banco de Horas acontece por `Agendamento` com motivo `BH`.

### TRE

- Usuario envia TRE com PDF obrigatorio.
- Administrador aprova, indefere, exclui ou lanca ajuste administrativo.
- Ajustes administrativos podem adicionar ou remover dias.
- `sync_tre_user(usuario_id)` recalcula total, usufruidas e restantes.
- Uploads de TRE ficam no diretorio persistente configurado por `UPLOAD_FOLDER`.

### Relatorios

- Relatorio de ponto com agendamentos e esquecimentos.
- Relatorio de horas extras.
- Relatorio/prontuario de servidores em PDF.
- Relatorio em lote com saida PDF ou ZIP.
- Geração de PDF com WeasyPrint e ReportLab.

### Eventos e avisos

- Administrador cria, edita e inativa eventos.
- Usuarios recebem aviso de novos eventos no acesso ao index.
- Administrador gerencia patch notes com severidades `info`, `improvement`, `fix` e `breaking`.

## Arquitetura

O projeto segue uma arquitetura Flask monolitica:

- `app.py` concentra configuracao, modelos SQLAlchemy, rotas, helpers, relatorios e integracoes.
- `templates/` contem paginas Jinja2.
- `static/` contem CSS, JavaScript e imagens.
- `migrations/` contem Flask-Migrate/Alembic.
- `uploads/` e `render_disk/` sao areas de arquivos gerados/persistentes.
- `backups/` contem scripts e dumps de banco.

Extensoes Flask inicializadas em `app.py`:

- `SQLAlchemy`
- `Migrate`
- `LoginManager`
- `CSRFProtect`

Banco suportado:

- PostgreSQL em producao.
- SQLite local como fallback quando `DATABASE_URL` nao esta definida e o ambiente nao e producao.

## Estrutura do projeto

```text
.
├── app.py                         # Aplicacao Flask principal
├── app-oficial.py                 # Copia/snapshot legado do app
├── requirements.txt               # Dependencias Python
├── Dockerfile                     # Imagem de producao com gunicorn
├── docker-compose.yml             # Ambiente local com Flask debug
├── Procfile                       # Start command simples para plataformas tipo Render/Heroku
├── run_sync.py                    # Script para recalcular TRE dos usuarios
├── criar_banco.py                 # Utilitario legado para criar tabelas
├── models.py                      # Arquivo vazio/legado
├── migrations/                    # Alembic/Flask-Migrate
├── templates/                     # Templates Jinja2
├── static/
│   ├── css/                       # Estilos
│   ├── js/                        # Scripts de UI/AJAX
│   └── img/                       # Logos e imagens
├── uploads/                       # Uploads locais e PDFs gerados
├── render_disk/                   # Simulacao local do Render Disk
├── instance/                      # SQLite local e arquivos de instancia
└── backups/                       # Scripts e dumps de backup
```

## Requisitos

- Python 3.10 ou superior.
- PostgreSQL para ambiente de producao.
- Dependencias listadas em `requirements.txt`.
- Para PDFs com WeasyPrint em Linux/Docker: Cairo, Pango, GDK Pixbuf, shared MIME info e fontes. O `Dockerfile` ja instala os pacotes necessarios.
- Para backup local de PostgreSQL: `pg_dump` e, opcionalmente, `pg_restore`.

## Configuracao local

No PowerShell, dentro da pasta do projeto:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Crie um `.env` local com valores reais. Nunca commite esse arquivo.

```env
FLASK_ENV=development
FLASK_DEBUG=1
PORT=8000

SECRET_KEY=troque-por-uma-chave-forte
SECURITY_PASSWORD_SALT=troque-por-um-salt-forte
PREFERRED_URL_SCHEME=http

# Opcional no dev. Se ausente, o app usa SQLite em instance/folgas.db.
DATABASE_URL=postgresql://usuario:senha@localhost:5432/folgas

# Uploads locais. Em producao no Render, prefira /var/data/uploads.
UPLOAD_FOLDER=uploads

BOTBOT_ENABLED=false
BOTBOT_SEND_TEXT_URL=https://botbot.chat/api/v2/sendText
BOTBOT_APP_KEY=
BOTBOT_AUTH_KEY=

SQLALCHEMY_POOL_RECYCLE=299
SQLALCHEMY_POOL_TIMEOUT=30

RESET_TOKEN_MAX_AGE=3600
EMAIL_CHANGE_MAX_AGE=3600

REPORT_ZIP_COMPRESSION=deflated
REPORT_ZIP_COMPRESSLEVEL=1
```

## Variaveis de ambiente

| Variavel | Uso |
| --- | --- |
| `DATABASE_URL` | URL do banco principal. Em producao e obrigatoria. |
| `SQLALCHEMY_DATABASE_URI` | Alternativa aceita pelo app para a URL do banco. |
| `SECRET_KEY` | Chave Flask para sessoes, CSRF e tokens. Obrigatoria em producao. |
| `SECURITY_PASSWORD_SALT` | Salt dos tokens de senha/e-mail. Obrigatoria em producao. |
| `UPLOAD_FOLDER` | Base de uploads e PDFs persistentes. |
| `PORT` | Porta usada por Docker/Render. |
| `FLASK_ENV` / `ENV` | Define modo de ambiente. `production` ativa exigencias de producao. |
| `PREFERRED_URL_SCHEME` | Esquema usado em links externos (`http` ou `https`). |
| `SESSION_COOKIE_SAMESITE` | Politica SameSite do cookie de sessao. Padrao: `Lax`. |
| `SESSION_COOKIE_SECURE` | Cookie de sessao apenas HTTPS. Padrao: true em producao. |
| `SQLALCHEMY_POOL_RECYCLE` | Reciclagem do pool em PostgreSQL. |
| `SQLALCHEMY_POOL_TIMEOUT` | Timeout do pool em PostgreSQL. |
| `BOTBOT_ENABLED` | Liga/desliga envio BotBot/WhatsApp. |
| `BOTBOT_SEND_TEXT_URL` | Endpoint de envio BotBot. |
| `BOTBOT_APP_KEY` | Chave da aplicacao BotBot. |
| `BOTBOT_AUTH_KEY` | Chave de autenticacao BotBot. |
| `RESET_TOKEN_MAX_AGE` | Validade do token de redefinicao de senha. |
| `EMAIL_CHANGE_MAX_AGE` | Validade do token de confirmacao de e-mail. |
| `REPORT_ZIP_COMPRESSION` | `deflated` ou `stored` para ZIP de relatorios. |
| `REPORT_ZIP_COMPRESSLEVEL` | Nivel de compressao do ZIP. Padrao: `1`. |

Observacao: o SMTP ainda esta configurado diretamente em `app.py`. O ideal e migrar `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` e `MAIL_FROM` para variaveis de ambiente antes de qualquer deploy publico.

## Banco de dados e migracoes

O app usa Flask-SQLAlchemy e Flask-Migrate. Os modelos ficam dentro de `app.py`.

O banco de produção deve ser tratado como fonte real de dados da unidade. Antes de aplicar migrations ou scripts de escrita em produção:

- confirme qual `DATABASE_URL` esta carregada no ambiente;
- gere backup recente e valide se o dump foi criado corretamente;
- teste a migration em ambiente local/staging quando possivel;
- evite `db.create_all()` em produção;
- não rode `run_sync.py`, scripts manuais ou updates em massa sem janela/validação.

Com o ambiente virtual ativo:

```powershell
python -m flask --app app.py db upgrade
```

Para criar uma nova migracao apos alterar modelos:

```powershell
python -m flask --app app.py db migrate -m "descricao_da_migracao"
python -m flask --app app.py db upgrade
```

Pontos importantes:

- Em desenvolvimento, se `DATABASE_URL` nao existir e o ambiente nao for producao, o app usa `sqlite:///instance/folgas.db`.
- Em producao, `DATABASE_URL` e `SECRET_KEY` sao obrigatorias.
- O app normaliza `postgres://` para `postgresql://`.
- Para hosts Render/Postgres, o app adiciona `sslmode=require` quando necessario.
- `criar_banco.py` e um utilitario legado. Para evolucao segura do schema, prefira migrations.

## Como executar

### Flask local

```powershell
.\.venv\Scripts\Activate.ps1
python -m flask --app app.py run --host=127.0.0.1 --port=8000 --debug
```

Acesse:

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/__health/db`

### Gunicorn

Em Linux/container:

```bash
gunicorn -b 0.0.0.0:${PORT:-8000} app:app --worker-class gthread --threads 4 --workers 1 --timeout 1800 --graceful-timeout 1800 --access-logfile - --error-logfile -
```

## Docker

Subir ambiente local com compose:

```powershell
docker compose up --build
```

O `docker-compose.yml`:

- usa `env_file: .env`;
- monta o codigo local em `/app`;
- expoe `8000:8000`;
- monta `./render_disk` em `/var/data`;
- roda Flask em modo debug.

## Deploy no Render

Configuracao recomendada:

- Build com o `Dockerfile` do projeto.
- Start command do Dockerfile ou equivalente gunicorn.
- PostgreSQL gerenciado no Render.
- Render Disk montado em `/var/data`.
- `UPLOAD_FOLDER=/var/data/uploads` para evitar caminhos duplicados como `tre/tre`.
- `PREFERRED_URL_SCHEME=https`.
- `SESSION_COOKIE_SECURE=true`.

Variaveis minimas de producao:

```env
ENV=production
DATABASE_URL=postgresql://...
SECRET_KEY=...
SECURITY_PASSWORD_SALT=...
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=true
UPLOAD_FOLDER=/var/data/uploads
```

Depois do deploy, validar:

- `/healthz`
- `/__health/db`
- login de administrador;
- upload/download de TRE;
- geracao de protocolo PDF;
- relatorio PDF;
- e-mail de recuperacao de senha, se SMTP estiver configurado.

## Uploads e arquivos persistentes

O app aceita PDF para TRE e gera protocolos PDF de agendamento.

Convencao atual:

```text
UPLOAD_FOLDER/
├── tre/
└── protocolos/
    └── agendamentos/
```

No Render, configure `UPLOAD_FOLDER=/var/data/uploads` e monte um disk em `/var/data`.

Rotas e helpers relevantes:

- Upload TRE: `/adicionar_tre`
- Download TRE: `/download_tre/<tre_id>`
- Protocolo: `/agendamentos/<agendamento_id>/protocolo`
- Debug de uploads para admin: `/__debug/uploads`
- Limite de upload: 20 MB
- Extensao permitida: `pdf`

## Relatorios e PDFs

Tecnologias:

- ReportLab para protocolos de agendamento.
- WeasyPrint para relatorios em PDF.
- ZIP nativo do Python para relatorios em lote.

Rotas de relatorio:

- `/relatorio_ponto`
- `/relatorio_horas_extras`
- `/user_info_report`
- `/user_info_report/<user_id>`
- `/user_info_report_count`
- `/user_info_report_stats`

Parametros importantes do relatorio de servidores:

- `scope`: `selected`, `filtered_all`, `ativos_all`, `all`, `single`.
- `types`: `AB`, `BH`, `TRE`, `LM`, `DL`, `DS`, `FS`, `OUTROS`.
- `dt_ini` e `dt_fim` no formato `AAAA-MM-DD`.
- `output`: `pdf` ou `zip`.
- `download=1` para baixar.
- `fetch=1` para resposta adequada a AJAX.

## Rotas principais

### Publicas ou sem login obrigatorio

| Rota | Descricao |
| --- | --- |
| `/login` | Login |
| `/register` | Registro de novo usuario |
| `/recuperar_senha` | Solicitar redefinicao de senha |
| `/redefinir_senha/<token>` | Redefinir senha por token |
| `/csrf-token` | Gerar token CSRF para frontend |
| `/healthz` | Healthcheck simples |
| `/__health/db` | Healthcheck de banco |

### Usuario autenticado

| Rota | Descricao |
| --- | --- |
| `/index` | Pagina inicial |
| `/termo_uso` | Aceite do termo vigente |
| `/logout` | Logout via POST |
| `/informar_dados` | Complemento de perfil obrigatorio |
| `/perfil` | Perfil e alteracao de e-mail |
| `/agendar` | Solicitar folga/justificativa |
| `/minhas_justificativas` | Historico pessoal de agendamentos |
| `/historico` | Historico de abonadas deferidas |
| `/calendario` | Calendario |
| `/relatar_esquecimento` | Relato de esquecimento de ponto |
| `/banco_horas` | Menu de banco de horas |
| `/banco_horas/cadastrar` | Cadastrar horas realizadas |
| `/consultar_horas` | Consultar banco de horas |
| `/tre` | Menu TRE |
| `/adicionar_tre` | Enviar TRE |
| `/minhas_tres` | Listar TREs do usuario |
| `/download_tre/<tre_id>` | Baixar PDF da TRE |

### Administrador

| Rota | Descricao |
| --- | --- |
| `/aprovar_usuarios` | Aprovar/rejeitar usuarios pendentes |
| `/admin/agendar_para` | Lancar agendamento para outro usuario |
| `/deferir_folgas` | Deferir/indeferir folgas |
| `/relatorio_ponto` | Relatorio de ponto |
| `/relatorio_horas_extras` | Relatorio de horas extras |
| `/admin/agendamentos` | Gestao administrativa de agendamentos |
| `/admin/agendamentos/ajax` | API AJAX de agendamentos |
| `/user_info_all` | Gestao/listagem de usuarios |
| `/admin/usuarios/<user_id>/atualizar` | Atualizar usuario |
| `/admin/user/<user_id>/alterar_email` | Alterar e-mail de usuario |
| `/toggle_user_ativo/<user_id>` | Ativar/inativar usuario |
| `/admin/users/search` | Busca AJAX de usuarios |
| `/banco_horas/inserir` | Inserir credito de BH como admin |
| `/banco_horas/deferir` | Deferir horas cadastradas |
| `/admin/tres` | Listar TREs |
| `/admin/tre/<tre_id>/decidir` | Aprovar/indeferir TRE |
| `/admin/tre/<tre_id>/excluir` | Excluir TRE |
| `/admin/tre/lancar` | Ajuste administrativo de TRE |
| `/admin/eventos` | Gerenciar eventos |
| `/admin/patch-notes` | Gerenciar patch notes |
| `/admin/horarios_trabalho` | Gerenciar horarios de trabalho |
| `/__debug/uploads` | Diagnostico de uploads |

## Backup

O projeto contem scripts em `backups/`:

- `backup_render.ps1`: script PowerShell mais seguro, usa a variavel `RENDER_DATABASE_URL`.
- `backup_folgas.bat`: script legado com credenciais fixas. Deve ser tratado como sensivel e evitado em novos fluxos.

Uso sugerido do script PowerShell:

```powershell
setx RENDER_DATABASE_URL "postgresql://usuario:senha@host:5432/banco?sslmode=require"
```

Abra um novo PowerShell e rode:

```powershell
.\backups\backup_render.ps1
```

O script cria dumps customizados (`.dump`) e aplica retencao local.

Para produção, prefira sempre backup antes de:

- `flask db upgrade`;
- ajustes manuais no banco;
- execução de scripts de sincronização;
- alteração de regras de saldo de TRE/BH;
- deploys que mudem modelos, migrations ou geração de arquivos persistentes.

## Seguranca e pontos de atencao

Pontos encontrados na analise do repositorio:

- Existem credenciais e dumps historicos versionados no repositorio. Antes de publicar ou compartilhar o projeto, rotacione segredos e remova artefatos sensiveis do historico Git.
- `SMTP_PASS` esta hardcoded em `app.py` e `app-oficial.py`. Migrar para variaveis de ambiente.
- `migrations/alembic.ini` contem URL de banco em texto claro. O `env.py` ja injeta a URL pelo app; prefira remover segredo fixo do `.ini`.
- Ha arquivos de runtime/cache versionados (`__pycache__`, `instance/folgas.db`, dumps). Avalie limpar o historico e reforcar `.gitignore`.
- A rota `/_smtp_diag` testa SMTP e nao exige login. Remova, proteja ou desative em producao.
- CSRF esta habilitado globalmente. Formularios e chamadas `fetch` devem enviar `csrf_token` ou header `X-CSRFToken`.
- O app tem validacao de mesma origem para metodos inseguros (`POST`, `PUT`, `PATCH`, `DELETE`).
- Cookies usam `SESSION_COOKIE_SECURE=true` por padrao em producao.

## Manutencao

### Verificacoes uteis

```powershell
python -m py_compile app.py
python -m flask --app app.py routes
python -m flask --app app.py db current
```

### Recalcular TRE

```powershell
python run_sync.py
```

### Boas praticas para mudancas

- Antes de alterar regra de negocio, localize a rota e os templates relacionados.
- Ao mexer em modelos, crie migracao Flask-Migrate.
- Ao mexer em TRE, chame ou preserve `sync_tre_user`.
- Ao mexer em LM, preserve o agrupamento por `lote_id`.
- Ao mexer em BH, mantenha saldo em minutos.
- Ao criar POST/AJAX, inclua CSRF.
- Ao criar upload/download, use `UPLOAD_FOLDER` e `secure_filename`.
- Ao alterar relatorios PDF, teste localmente com WeasyPrint instalado ou via Docker.
