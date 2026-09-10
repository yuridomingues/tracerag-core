# SaaS readiness

O TraceRAG Core ainda e um nucleo tecnico. Ele pode sustentar um SaaS, mas nao deve ser vendido como plataforma multi-tenant pronta antes das camadas abaixo existirem.

## O que ja existe

- isolamento logico por `project_id` no indice vetorial;
- retrieval com origem, chunk e distancia;
- abstencao quando nao existe evidencia suficiente;
- benchmark de retrieval reproduzivel;
- API versionada;
- testes automatizados e CI.

## O que falta antes de clientes reais

### Identidade e tenancy

- autenticacao;
- workspaces e membros;
- autorizacao por projeto;
- isolamento forte de dados por tenant;
- rotacao e armazenamento seguro de credenciais.

### Dados

- upload por object storage em vez de caminho local;
- politica de retencao e exclusao;
- versionamento de datasets e documentos;
- migracao do armazenamento experimental para componentes gerenciados quando necessario.

### Operacao

- rate limiting;
- logs estruturados sem vazar conteudo sensivel;
- metricas de latencia e custo;
- healthchecks de dependencias;
- backup e recuperacao;
- deploy reproduzivel.

### Produto

- onboarding;
- criacao de datasets de avaliacao pela interface ou API;
- baseline versionado;
- comparacao entre experimentos;
- gate de CI configuravel;
- billing somente depois de existir uso repetido.

## Ordem recomendada

1. validar o problema com 5 a 10 equipes que ja possuem RAG;
2. integrar um pipeline externo real;
3. provar que o produto detecta uma regressao que seria dificil de perceber manualmente;
4. adicionar tenancy e armazenamento para um piloto pago;
5. adicionar billing apenas quando o fluxo de uso estiver repetido.

A decisao principal e evitar construir uma plataforma de observabilidade generica. A proposta e ser uma ferramenta de regression testing de RAG pequena, auditavel e simples de colocar em CI.
