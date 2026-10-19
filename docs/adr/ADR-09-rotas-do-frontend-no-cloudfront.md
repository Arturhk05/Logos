# ADR-09: Rotas do frontend no CloudFront

- **Status:** Aceito
- **Data:** 2026-10-19

## Contexto

O frontend usa URLs reais para as telas e para os filtros (`/fila/<id>`, `/historico?page=2`, `/meus-reportes`), o que permite recarregar a página e compartilhar um link (US-02). Quem resolve essas rotas é o React Router, no navegador. No servidor existe apenas o build: um `index.html` e os arquivos de `assets/`.

O CloudFront serve o frontend a partir de um S3 privado e a API a partir da EC2, no mesmo domínio (ADR-01). Ao abrir `/fila/123` direto, o CloudFront pede ao S3 o objeto `fila/123`, que não existe. Como o CloudFront não tem permissão para listar o bucket, o S3 responde `403` em vez de `404`, e a pessoa vê um erro em XML no lugar da tela.

O frontend depende dos códigos de resposta da API: o `ApiError` decide o que mostrar a partir deles (sessão expirada, sem permissão, incidente inexistente, conflito de versão). Qualquer solução para as rotas do React não pode alterar as respostas de `/api/*`.

## Decisão

Uma **CloudFront Function** (`logos-spa-routes`), no evento `viewer-request`, associada **apenas ao comportamento padrão** (`/*`, origem S3):

- Se o último trecho do caminho não tem ponto (`/`, `/fila`, `/fila/123`, `/meus-reportes`), a função troca o caminho por `/index.html`, e o React Router abre a tela certa.
- Se tem ponto (`/index.html`, `/assets/index-abc.js`), o caminho segue sem alteração. Um arquivo inexistente continua respondendo erro, em vez de devolver HTML no lugar de um script.

O comportamento `/api/*` não tem função associada: as respostas da API chegam ao navegador como saíram dela.

A query string não é alterada, então os filtros na URL continuam chegando ao React.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Respostas de erro personalizadas do CloudFront** (403 e 404 → `/index.html` com 200) | É a forma mais comum, mas vale para a distribuição inteira, inclusive `/api/*`. Um incidente inexistente (404) ou uma ação sem permissão (403) viraria `200` com o HTML da página, e o frontend deixaria de mostrar a mensagem certa. |
| **Hospedagem de site estático do S3** (documento de erro = `index.html`) | Exige um bucket público, o que desfaz o acesso exclusivo pelo CloudFront via OAC. |

## Consequências

**Positivas**

- Recarregar ou abrir um link de qualquer tela funciona.
- As respostas da API não mudam, e o tratamento de erros do frontend continua valendo.
- A função roda nos servidores de borda do CloudFront e não tem custo dentro do plano gratuito (2 milhões de invocações por mês).

**Negativas**

- Mais um recurso para criar, publicar e apagar junto com a distribuição.
- Uma rota do React com ponto no último trecho (por exemplo, `/relatorios/2026.10`) seria tratada como arquivo e daria erro. Nenhuma rota atual tem ponto; uma rota assim exigiria mudar a regra da função.
- Um caminho sem ponto que não é rota do React (por exemplo, `/qualquer-coisa`) recebe o `index.html`, e o próprio React decide o que mostrar: hoje, o redirecionamento para a tela inicial do papel.
