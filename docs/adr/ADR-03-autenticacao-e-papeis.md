# ADR-03: Autenticação e controle de acesso por papéis

- **Status:** Aceito
- **Data:** 2026-10-17

## Contexto

O Logos tem três papéis com permissões diferentes:

| Papel | Permissões |
|---|---|
| Analista | Ver todos os incidentes, assumir, alterar os que assumiu. |
| Supervisor | Tudo do analista, mais alterar qualquer incidente. |
| Motorista | Criar incidentes e ver apenas os que reportou. |

Frontend e API são servidos pelo **mesmo domínio** (`logos.arturkrauspenhar.com.br`), via CloudFront (ADR-01): o frontend em `/` e a API em `/api/*`.

## Decisão

- **Autenticação com JWT** armazenado em **cookie `httpOnly`**, definido pela API no login:

  ```
  Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/api; Max-Age=28800
  ```

  | Atributo | Finalidade |
  |---|---|
  | `HttpOnly` | O JavaScript da página não consegue ler o token, o que impede seu roubo em caso de XSS. |
  | `Secure` | O cookie só trafega por HTTPS. |
  | `SameSite=Strict` | O navegador não envia o cookie em requisições originadas de outros sites, o que protege contra CSRF. |
  | `Path=/api` | O cookie só é enviado nas chamadas à API. |
  | `Max-Age=28800` | Expira em **8 horas**, a mesma validade do token. |

- O token contém apenas o identificador do usuário (`sub`), a data de emissão (`iat`) e a expiração (`exp`). O papel não vai no token:
  - a cada requisição, a API busca o usuário no banco e usa o papel que está lá. Uma mudança de papel ou a remoção do usuário vale na requisição seguinte, sem esperar o token expirar;
  - o frontend não consegue ler o token (cookie `HttpOnly`) e recebe o papel pela resposta do login e do `GET /api/me`.
- Senhas armazenadas com hash **bcrypt**.
- Endpoints de autenticação:
  - `POST /api/auth/login`: valida as credenciais e define o cookie.
  - `POST /api/auth/logout`: remove o cookie.
  - `GET /api/me`: retorna o usuário autenticado e seu papel, usado pelo frontend para montar a interface.
- O frontend não armazena nem manipula o token: o navegador envia o cookie automaticamente. Ao receber 401, o usuário é redirecionado ao login.
- No CloudFront, o comportamento `/api/*` usa as políticas `CachingDisabled` e `AllViewerExceptHostHeader`, para que os cookies cheguem à API e nenhuma resposta autenticada fique em cache.

- Usuários criados por *seed* (sem tela de cadastro no MVP). As credenciais de demonstração de cada papel ficam visíveis na tela de login.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **JWT no `localStorage`** com cabeçalho `Authorization` | Qualquer script na página consegue ler o token. Em caso de XSS ou de dependência comprometida, o token é roubado e pode ser usado de qualquer lugar até expirar. |
| **Sessão no servidor com cookie** | Igualmente segura no navegador, mas exige armazenar sessões (tabela ou Redis) e consultá-las a cada requisição. O JWT dispensa esse armazenamento. |
| **Provedor externo** (Auth0, Clerk, Cognito) | Mais uma dependência e configuração, e esconde a lógica de permissões que o desafio quer ver. |
| **Somente chave de API** | Não identifica o usuário individual, e as regras de negócio precisam disso. |

## Consequências

**Positivas**

- O token não fica acessível ao JavaScript da página, então não pode ser roubado via XSS.
- Proteção contra CSRF pelo `SameSite=Strict`, viável porque frontend e API estão na mesma origem.
- Logout efetivo no navegador: a API remove o cookie.
- Permissões centralizadas e testáveis no backend.

**Negativas**

- O cookie não elimina o XSS: um script malicioso ainda pode fazer requisições em nome do usuário enquanto a página estiver aberta, apesar de não conseguir levar o token. **Mitigação:** Não usar `dangerouslySetInnerHTML`.
- Não há revogação do token no servidor antes de expirar. Aceitável para o MVP.
- Depende de frontend e API na mesma origem. Separá-los em domínios diferentes exigiria rever `SameSite` e adicionar proteção explícita contra CSRF.
- Configuração do CloudFront precisa repassar cookies para `/api/*`. Se esquecida, o login parece funcionar, mas as requisições seguintes chegam sem autenticação.
