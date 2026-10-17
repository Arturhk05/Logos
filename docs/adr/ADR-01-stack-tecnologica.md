# ADR-01: Stack tecnológica

- **Status:** Aceito
- **Data:** 2026-10-17

## Contexto

O desafio define que a API deve ser em **Python** e a interface em **React**, com persistência em banco de dados ou JSON estruturado, e com a aplicação publicada em nuvem.

Requisitos que influenciam a escolha:

- Validação consistente de todas as entradas.
- Controle de concorrência no banco.
- Interface que lide bem com carregamento, erro, cache e falhas de rede (RNF-03).
- Prazo curto.
- Hospedagem em nuvem com custo baixo, coberta por créditos da AWS (US$ 100), e oportunidade de aprofundar conhecimento em AWS.

## Decisão

### Backend

| Tecnologia | Papel | Motivo |
|---|---|---|
| **FastAPI** | Framework web | Validação automática via Pydantic, documentação OpenAPI gerada (Swagger), suporte a async, injeção de dependências. Maior familiaridade com o framework. |
| **Pydantic** | Validação de entrada e saída | Schemas tipados, dados inválidos viram erro 422 descritivo, nunca erro 500. |
| **SQLAlchemy** | ORM | Suporta `UPDATE` condicional e transações explícitas. |
| **Alembic** | Migrações | Versionamento do schema do banco. |
| **PostgreSQL** | Banco de dados | Transações ACID e garantias de concorrência confiáveis. |
| **pytest** | Testes | Já tenho familiaridade, o que reduz risco num prazo curto. Além disso, é o padrão de mercado em Python, tem fixtures para isolar banco e usuários entre testes. |

### Frontend

| Tecnologia | Papel | Motivo |
|---|---|---|
| **React + Vite** | Base da aplicação | Exigência do desafio e Vite tem build e ambiente de desenvolvimento rápidos. |
| **TypeScript** | Tipagem | Contratos claros com a API e menos erros em tempo de execução. |
| **TanStack Query** | Estado do servidor | Cache, novas tentativas automáticas, estados de loading e erro e atualização otimista com rollback prontos, o que atende diretamente ao RNF-03. |
| **Tailwind CSS** | Estilização | Produtividade, consistência de espaçamento e tema escuro com a variante `dark:`. |
| **React Router** | Navegação | Rotas por papel e filtros persistidos na URL (US-02). |

### Hospedagem

Aplicação hospedada na **AWS** (região `us-east-1`), acessível em `https://logos.arturkrauspenhar.com.br`.

```
                 ┌──────────────── CloudFront (HTTPS) ────────────────┐
 usuário ──────► │  /*      → S3 (build do React)                     │
                 │  /api/*  → EC2 (container FastAPI)                 │
                 └────────────────────────────────────────────────────┘
                                         │
                                         ▼
                                RDS PostgreSQL
```

| Parte | Serviço | Motivo |
|---|---|---|
| CDN e HTTPS | **CloudFront** | Ponto único de entrada: serve frontend e API no mesmo domínio, com HTTPS. |
| Certificado | **ACM** (em `us-east-1`) | Certificado gratuito com renovação automática, exigido pelo CloudFront. |
| Frontend | **S3** | Arquivos estáticos do build, acessíveis apenas pelo CloudFront via OAC (*Origin Access Control*). |
| API | **EC2** (t4g.micro ou t3.micro) com Docker | Custo baixo e controle total do ambiente. |
| Imagens Docker | **ECR** | Registro privado das imagens da API. |
| Banco de dados | **RDS PostgreSQL** (db.t4g.micro) | Banco gerenciado com backup automático, em subnet privada, acessível apenas pela EC2. |
| Logs | **CloudWatch** | Logs da API e alarmes básicos. |
| DNS | Registro `CNAME` de `logos` apontando para o CloudFront, no provedor DNS atual do domínio. | Mantém o domínio principal onde está. |

Deploy automatizado com **GitHub Actions**, autenticado na AWS via **OIDC** (sem chaves de acesso armazenadas no repositório).

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Django + DRF** | Mais completo, mas mais pesado e com mais convenções do que o MVP precisa. |
| **Flask** | Exige montar validação, documentação e injeção de dependências manualmente. |
| **JSON estruturado como persistência** | Permitido pelo desafio, mas não oferece transações nem escrita atômica, o que inviabiliza o controle de concorrência na alteração de incidentes com segurança. |
| **Vercel + Render + Neon** | Planos gratuitos e deploy mais simples, mas a API hiberna após inatividade e não há aprendizado de AWS. |

## Consequências

**Positivas**

- Validação, documentação da API e tratamento de estados de rede vêm em grande parte das próprias bibliotecas.
- PostgreSQL garante a atomicidade necessária ao controle de concorrência.
- API sempre ativa, sem atraso de "despertar" na primeira requisição.
- Banco de dados sem exposição à internet.

**Negativas**

- Mais complexidade: atualização do sistema da EC2, configuração de rede e permissões IAM ficam a cargo do projeto.
- Custo recorrente. **Mitigação:** alertas no AWS Budgets e remoção dos recursos ao fim da avaliação.
- EC2 única é ponto único de falha. Aceitável para o MVP. A evolução natural é ECS com mais de uma tarefa atrás de um load balancer.
