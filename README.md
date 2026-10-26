# Ingestão e Busca Semântica com LangChain e PostgreSQL

Aplicação de **RAG (Retrieval-Augmented Generation)** desenvolvida em Python para responder perguntas sobre o conteúdo de um arquivo PDF, usando **LangChain**, **OpenAI**, **PostgreSQL** e **pgVector**.

O documento é dividido em trechos, transformado em embeddings e armazenado em um banco vetorial. Na consulta, a aplicação recupera os trechos semanticamente mais relevantes e solicita à LLM uma resposta **limitada ao conteúdo recuperado**. Quando não há informação suficiente, o comportamento esperado é responder:

> Não tenho informações necessárias para responder sua pergunta.

Este projeto implementa o desafio [Ingestão e Busca Semântica com LangChain e Postgres](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca), da Full Cycle.

## Tecnologias

- Python 3 (validado localmente com Python 3.14.5)
- LangChain e integrações `langchain-openai` e `langchain-postgres`
- OpenAI: `text-embedding-3-small` para embeddings e `gpt-4.1-mini` para respostas (valores padrão do código)
- PostgreSQL 16 com extensão pgVector
- Docker Desktop e Docker Compose
- `PyPDFLoader` e `RecursiveCharacterTextSplitter`

> **Custos:** a API OpenAI possui faturamento separado da assinatura ChatGPT. É necessário usar uma API Key com créditos ou faturamento disponível. Consulte o [painel da API](https://platform.openai.com/settings/organization/billing/overview).

## Estrutura do projeto

```text
mba-ia-desafio-ingestao-busca/
├── docker-compose.yml        # PostgreSQL com pgVector
├── requirements.txt          # Dependências Python
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore                # Arquivos excluídos do versionamento
├── document.pdf              # Documento utilizado na ingestão
├── src/
│   ├── ingest.py             # Leitura, fragmentação e indexação do PDF
│   ├── search.py             # Busca vetorial e geração de respostas
│   └── chat.py               # Interface de chat no terminal
└── README.md
```

## Pré-requisitos

- Git
- Python 3 e `pip`
- Docker Desktop com Docker Compose (no Windows, com WSL 2 funcionando)
- Conta na OpenAI com API Key válida e saldo disponível

## Instalação e execução

Os exemplos a seguir utilizam **PowerShell no Windows**. Execute os comandos na **raiz do projeto**.

### 1. Clonar o repositório

```powershell
git clone https://github.com/wandrelito/mba-ia-desafio-ingestao-busca.git
cd mba-ia-desafio-ingestao-busca
```

### 2. Criar e ativar o ambiente virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se a ativação estiver bloqueada pela política de execução do PowerShell, execute **na sessão atual**:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

No Linux ou macOS, a ativação é feita com `source venv/bin/activate`.

### 3. Configurar as variáveis de ambiente

Crie um `.env` a partir do modelo:

```powershell
Copy-Item .env.example .env
```

Configure no `.env` os nomes de variáveis **utilizados pelo código desta implementação**:

```dotenv
OPENAI_API_KEY=COLOQUE_SUA_CHAVE_AQUI
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4.1-mini
DATABASE_URL=postgresql+psycopg://raguser:ragpassword@localhost:5432/ragdb
PGVECTOR_COLLECTION=pdf_document
PDF_PATH=document.pdf
```

**Atenção:** o `.env.example` presente no repositório original pode conter `PG_VECTOR_COLLECTION_NAME`. Nesta implementação, o `search.py` utiliza **`PGVECTOR_COLLECTION`** (sem `_` após `PG`). Caso o modelo ainda não tenha sido atualizado, use os nomes listados acima e atualize o `.env.example` antes de entregar.

Nunca publique o arquivo `.env` ou sua chave de API. A senha `ragpassword` é **apenas para desenvolvimento local** e corresponde à configuração fornecida no `docker-compose.yml`. Não exponha este banco à internet.

### 4. Iniciar o PostgreSQL com pgVector

Abra o Docker Desktop e confirme que o Docker Engine está ativo. Em seguida:

```powershell
docker compose up -d
docker compose ps
```

O serviço `postgres` utiliza o banco `ragdb`, o usuário `raguser` e a porta `5432` do computador. Para conferir os logs:

```powershell
docker compose logs --tail=30 postgres
```

Habilite a extensão no banco, se ainda não estiver habilitada:

```powershell
docker compose exec postgres psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Confira a extensão:

```powershell
docker compose exec postgres psql -U raguser -d ragdb -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### 5. Preparar o PDF

Coloque o documento na **raiz do projeto**, com o nome `document.pdf`. Se quiser usar outro nome, ajuste `PDF_PATH` no `.env`.

### 6. Executar a ingestão

```powershell
python src/ingest.py
```

O script lê o arquivo, extrai o texto, cria chunks de **1.000 caracteres com overlap de 150**, gera embeddings pela OpenAI e grava os vetores no pgVector.

Exemplo de execução local com um PDF de 36 páginas:

```text
Ingestão concluída: 36 páginas, 63 trechos.
```

A quantidade depende do documento utilizado. Para conferir os vetores armazenados:

```powershell
docker compose exec postgres psql -U raguser -d ragdb -c "SELECT COUNT(*) AS total_vetores FROM langchain_pg_embedding;"
```

### 7. Conversar com o documento

```powershell
python src/chat.py
```

Exemplo de sessão **observada nos testes locais** com o PDF *A Herança de Si Mesmo*:

```text
Chat com PDF. Digite sair para encerrar.

Faça sua pergunta: qual o titulo do documento?
RESPOSTA: O título do documento é "A Herança de Si Mesmo".

Faça sua pergunta: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.

Faça sua pergunta: sair
```

Para encerrar, digite `sair` (também são aceitos `exit` e `quit`). As respostas variam conforme o PDF indexado e os trechos recuperados.

## Como funciona

**Ingestão:** `document.pdf` → `PyPDFLoader` → `RecursiveCharacterTextSplitter` (1.000/150) → `OpenAIEmbeddings` → `PGVector`.

**Consulta:** pergunta no terminal → embedding da pergunta → `similarity_search_with_score(pergunta, k=10)` → concatenação dos trechos → prompt restritivo → `ChatOpenAI` → resposta.

O parâmetro **`k=10`** significa recuperar **até dez** trechos; se o banco tiver menos documentos/trechos, a consulta poderá retornar menos resultados. O prompt instrui a LLM a usar somente o contexto e a não inventar informações. Como em qualquer sistema com LLM, essa instrução **reduz o risco de alucinação, mas não garante precisão absoluta**; respostas importantes devem ser conferidas no documento original.

## Testes realizados

- Ingestão de um PDF de 36 páginas com **63 trechos** e **63 registros** de embeddings no banco vetorial.
- Resposta factual sobre o título do PDF.
- Resposta resumida sobre os assuntos tratados no documento.
- Pergunta fora do contexto retornando a mensagem padrão exigida pelo desafio.

Esses são testes manuais locais, não uma suíte de testes automatizados.

## Solução de problemas

| Problema | Possível causa e ação |
| --- | --- |
| `PDF não encontrado` | Confira a localização de `document.pdf` na raiz ou o valor de `PDF_PATH`. |
| `role "postgres" does not exist` | O usuário configurado é `raguser`. Use `-U raguser -d ragdb`. |
| Erro de conexão com PostgreSQL | Abra o Docker Desktop, confira `docker compose ps` e valide `DATABASE_URL`. |
| Erro OpenAI `429` / `credit_balance_exhausted` | Verifique o saldo e o faturamento da API OpenAI. |
| `DeprecationWarning` de `langchain-community` | Aviso de biblioteca em descontinuação; não impede, por si só, a execução observada. |
| Erro de dimensão dos embeddings | Um modelo de embeddings diferente pode produzir outra dimensão vetorial; recrie a indexação/coleção compatível. |
| Respostas referentes a um PDF anterior | A implementação não faz a substituição automática dos embeddings antigos; para um ambiente de teste de documento único, limpe os registros antigos antes de reingerir. |

Para **substituir integralmente os vetores** em um ambiente de teste com apenas um documento, é possível usar o comando abaixo **antes da nova ingestão**:

```powershell
docker compose exec postgres psql -U raguser -d ragdb -c "TRUNCATE TABLE langchain_pg_embedding;"
python src/ingest.py
```

> **Cuidado:** `TRUNCATE` apaga **todos** os embeddings dessa tabela. Não utilize esse procedimento se houver dados que precisem ser preservados. A substituição automática de PDFs não faz parte dos requisitos do desafio.

## Encerrar o ambiente

```powershell
docker compose down
```

Esse comando encerra e remove os contêineres da composição, preservando o volume nomeado com os dados. **Não execute `docker compose down -v` se quiser conservar o banco.**

## Referências

- [Desafio original — Full Cycle](https://github.com/devfullcycle/mba-ia-desafio-ingestao-busca)
- [LangChain](https://python.langchain.com/)
- [Integração PGVector do LangChain](https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector)
- [Documentação da API OpenAI](https://platform.openai.com/docs/)
- [pgVector](https://github.com/pgvector/pgvector)

## Observações

Projeto desenvolvido com finalidade educacional. A aplicação utiliza credenciais locais demonstrativas para PostgreSQL, e o processamento de embeddings e respostas utiliza a API OpenAI. O arquivo PDF incluído no repositório deve ser um documento que possa ser redistribuído publicamente.
