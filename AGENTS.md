# AGENTS.md

Guia para agentes de IA e mantenedores trabalhando neste repositório.

## Contexto do projeto

Este repositório contém um sistema Flask monolítico chamado `Folga System`, usado como central administrativa de uma unidade escolar. Ele cobre cadastro de servidores, aprovação de usuários, solicitações de folga, banco de horas, TRE, esquecimento de ponto, calendário, eventos, patch notes, relatórios e PDFs.

Importante: este sistema está em produção e o banco usado no deploy é de produção. Qualquer operação que possa escrever, migrar, recalcular, remover, restaurar ou sobrescrever dados deve ser tratada como sensível e exigir confirmação clara do usuário.

O arquivo principal é `app.py`. Ele concentra:

- configuração Flask;
- inicialização de extensões;
- modelos SQLAlchemy;
- rotas;
- helpers de negócio;
- geração de PDFs;
- envio de e-mail;
- integração BotBot/WhatsApp.

`app-oficial.py` parece ser uma cópia/snapshot legado. Não use como entrypoint sem pedido explícito. `models.py` está vazio/legado.

## Regras de trabalho

- Responda e documente preferencialmente em pt-BR.
- Antes de editar, rode `git status --short` e entenda se há mudanças do usuário.
- Não reverta mudanças que você não fez.
- Prefira `rg`/`rg --files` para localizar arquivos e trechos.
- Use edições pequenas e coerentes com o estilo existente.
- Não faça refatorações amplas no monólito sem pedido claro.
- Não mova modelos para outro arquivo sem planejar migração e imports.
- Não altere `app-oficial.py` só porque alterou `app.py`, a menos que o usuário peça sincronização.
- Não commite, não rode comandos destrutivos e não remova backups sem autorização.
- Não rode migrations, seeds, scripts de sincronização ou comandos de escrita apontando para produção sem confirmação explícita.
- Antes de qualquer ação em banco de produção, recomende backup e confirme qual ambiente/URL será usado, sem expor segredos.

## Entry points e comandos

Aplicação:

```powershell
python -m flask --app app.py run --host=127.0.0.1 --port=8000 --debug
```

Docker local:

```powershell
docker compose up --build
```

Migrações:

```powershell
python -m flask --app app.py db migrate -m "descricao"
python -m flask --app app.py db upgrade
```

Verificações rápidas:

```powershell
python -m py_compile app.py
python -m flask --app app.py routes
python -m flask --app app.py db current
```

Recalcular saldos de TRE:

```powershell
python run_sync.py
```

## Arquitetura e padrões locais

Extensões globais:

- `db = SQLAlchemy()`
- `migrate = Migrate()`
- `login_manager = LoginManager()`
- `csrf = CSRFProtect()`

Não crie uma segunda instância dessas extensões.

Modelos principais em `app.py`:

- `User`
- `Agendamento`
- `Folga`
- `BancoDeHoras`
- `EsquecimentoPonto`
- `TRE`
- `Evento`
- `EventoVisto`
- `ReleaseNote`
- `ReleaseNoteRead`
- `UserHorarioTrabalho`

Templates ficam em `templates/`. CSS/JS/imagens ficam em `static/`.

## Autenticação e autorização

- Login usa Flask-Login.
- Usuários têm `tipo`: normalmente `funcionario` ou `administrador`.
- Usuários têm `status`: `pendente`, `aprovado` ou `rejeitado`.
- Usuários podem ser inativados por `ativo=False`.
- Rotas autenticadas devem usar `@login_required`.
- Rotas administrativas devem validar `current_user.tipo == "administrador"` ou usar o decorator `admin_required` adequado ao trecho.
- Existem mais de uma definição de `admin_required` em `app.py`; antes de alterar, leia o bloco da rota que será afetada.

## CSRF e segurança de formulário

CSRF está habilitado globalmente.

Para formulários Jinja:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

Para `fetch`/AJAX:

```javascript
headers: { "X-CSRFToken": csrf }
```

O app também valida `Origin`/`Referer` em métodos inseguros. Ao criar chamadas AJAX novas, preserve `credentials: "same-origin"` quando necessário.

## Regras de negócio críticas

Motivos de agendamento conhecidos:

- `AB`: Abonada
- `BH`: Banco de Horas
- `TRE`: TRE
- `LM`: Licença Médica
- `DS`: Doação de Sangue
- `FS`: Falta Simples
- `DL`: Dispensa Legal

Preserve estas invariantes:

- `AB` tem limite de uma solicitação ativa por mês e seis deferidas por ano.
- `BH` usa minutos como unidade interna. `User.banco_horas` é saldo em minutos.
- Créditos de BH ficam em `BancoDeHoras`; consumo/usufruto fica em `Agendamento` com motivo `BH`.
- `TRE` precisa passar por `sync_tre_user(usuario_id)` após alterações em TRE ou agendamentos TRE.
- `TRE` aceita ajustes administrativos negativos.
- `LM` por período cria vários `Agendamento`, um por dia, com o mesmo `lote_id`.
- Relatórios agrupam LM por `lote_id`; não quebre esse agrupamento.
- Campos `conferido` em agendamentos/esquecimentos são usados em relatórios.
- `tipo_folga` e `motivo` costumam ser mantidos sincronizados.

## Uploads e PDFs

Use sempre `UPLOAD_FOLDER` como base.

Convenção:

```text
UPLOAD_FOLDER/
├── tre/
└── protocolos/
    └── agendamentos/
```

Helpers relevantes:

- `allowed_file`
- `_upload_base_dir`
- `_ensure_upload_subdir`
- `_tre_dir`
- `_protocolos_dir`
- `_ensure_upload_dir`
- `_resolve_pdf_path`
- `_protocolo_agendamento_abs_path`

Regras:

- Apenas PDF é permitido para TRE.
- Limite atual: 20 MB.
- Use `secure_filename`.
- Não grave uploads em `static/`.
- Em Render, prefira `UPLOAD_FOLDER=/var/data/uploads`.

## E-mail e BotBot

O app envia e-mails por SMTP/Gmail e mensagens pelo BotBot.

Cuidados:

- Não adicione novos segredos hardcoded.
- O SMTP atual ainda está hardcoded em `app.py`; se tocar nesse trecho, migre para env vars ou mantenha compatibilidade.
- Falhas de BotBot não devem derrubar o fluxo principal.
- Em fluxos com e-mail obrigatório, registre logs claros e retorne mensagem amigável.
- Links externos dependem de `PREFERRED_URL_SCHEME`, `SECRET_KEY` e `SECURITY_PASSWORD_SALT`.

## Banco de dados e migrações

- Use Flask-Migrate/Alembic.
- Modelos estão em `app.py`.
- Ao alterar schema, gere migration.
- Teste migration em banco local antes de aplicar em produção.
- O banco de produção contém dados reais. Não execute `flask db upgrade`, SQL manual, `db.create_all()`, restore ou scripts de massa nele sem autorização explícita.
- Antes de produção, peça/garanta backup recente e plano de rollback.
- Não edite dumps SQL para "consertar" schema se migrations resolvem.
- `criar_banco.py` é legado; prefira `flask db upgrade`.
- `migrations/alembic.ini` possui configuração sensível legada. Não copie segredos dele para documentação ou respostas.

## Relatórios

Relatórios usam ReportLab e WeasyPrint.

Rotas relevantes:

- `/relatorio_ponto`
- `/relatorio_horas_extras`
- `/user_info_report`
- `/user_info_report/<user_id>`
- `/user_info_report_count`
- `/user_info_report_stats`

Ao alterar relatórios:

- teste geração PDF;
- teste `fetch=1` para erros em modal/AJAX;
- preserve filtros `dt_ini`, `dt_fim`, `types`, `scope`, `output` e `download`;
- preserve a otimização de ZIP (`REPORT_ZIP_COMPRESSION`, `REPORT_ZIP_COMPRESSLEVEL`);
- valide LM por período.

## Frontend

O frontend é composto por templates Jinja grandes, CSS local e JavaScript local/inline.

Antes de mexer em UI:

- localize o template da rota;
- procure scripts inline no próprio template;
- verifique se há CSS específico em `static/css`;
- preserve tokens CSRF em forms e AJAX;
- teste em desktop e largura menor quando a tela for densa.

Templates relevantes:

- `login.html`, `register.html`, `perfil.html`
- `index.html`
- `agendar.html`
- `minhas_justificativas.html`
- `calendario.html`
- `deferir_folgas.html`
- `menu_banco_horas.html`, `cadastrar_horas.html`, `consultar_horas.html`, `deferir_horas.html`, `inserir_bh_admin.html`
- `tre_menu.html`, `adicionar_tre.html`, `minhas_tres.html`, `admin_tres.html`, `admin_tre_lancar.html`
- `user_info_all.html`
- `relatorio_ponto.html`, `relatorio_horas_extras.html`, `relatorio_servidores.html`
- `admin_eventos.html`, `admin_patch_note.html`, `admin_horarios_trabalho.html`

## Deploy

Produção normalmente roda via Gunicorn.

O `Dockerfile` usa:

```bash
gunicorn -b 0.0.0.0:${PORT:-8000} app:app --worker-class gthread --threads 4 --workers 1 --timeout 1800 --graceful-timeout 1800 --access-logfile - --error-logfile -
```

No Render:

- configurar `DATABASE_URL`;
- configurar `SECRET_KEY`;
- configurar `SECURITY_PASSWORD_SALT`;
- configurar `UPLOAD_FOLDER=/var/data/uploads`;
- montar disk em `/var/data`;
- usar HTTPS e `SESSION_COOKIE_SECURE=true`.

Validar depois do deploy:

- `/healthz`
- `/__health/db`
- login admin;
- upload/download TRE;
- protocolo de agendamento;
- relatório PDF;
- envio de e-mail, se aplicável.

## Segredos e dados sensíveis

Este repositório contém histórico/arquivos sensíveis versionados, incluindo dumps e credenciais legadas.

Regras para agentes:

- Nunca exiba valores reais de `.env`, URLs de banco, senhas, tokens ou dumps em respostas.
- Não leia `.env` completo se só precisar dos nomes das variáveis.
- Não inclua segredos em README, issues, commits ou logs.
- Se encontrar segredo hardcoded, avise de forma resumida e recomende rotação.
- Trate `backups/`, `instance/`, `migrations/alembic.ini` e scripts legados como potencialmente sensíveis.

## Coisas para não fazer sem pedido explícito

- Não apagar `backups/`.
- Não apagar `instance/folgas.db`.
- Não rodar comandos que escrevam no banco de produção.
- Não rodar `flask db upgrade` em produção.
- Não rodar `run_sync.py` contra produção.
- Não restaurar dump sobre produção.
- Não remover `app-oficial.py`.
- Não reformatar `app.py` inteiro.
- Não dividir o monólito em pacote.
- Não mudar nomes de status/motivos sem migração e atualização de templates.
- Não desativar CSRF.
- Não transformar uma falha de BotBot em erro fatal.
- Não alterar regras de saldo de BH/TRE sem validar relatórios.

## Checklist antes de finalizar uma mudança

- `git status --short` revisado.
- Mudanças limitadas ao escopo pedido.
- Rotas alteradas continuam com autenticação/autorização correta.
- Forms e AJAX continuam com CSRF.
- Se modelo mudou, migration criada.
- Se TRE mudou, `sync_tre_user` preservado.
- Se BH mudou, saldo em minutos preservado.
- Se LM mudou, `lote_id` e agrupamento preservados.
- Se upload mudou, `UPLOAD_FOLDER` e `secure_filename` usados.
- Pelo menos uma verificação local executada ou limitação reportada.
