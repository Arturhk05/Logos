# ADR-04: Limitação de taxa de requisições (rate limit)

- **Status:** Retirado do escopo do MVP
- **Data:** 2026-10-17

> **Situação:** o rate limit não foi implementado no MVP. O tempo foi para as telas, que pesam mais na avaliação, e o login, os papéis e a validação das entradas já cobrem a segurança básica da API. A decisão abaixo fica registrada para quando o limite for implementado. A exceção é o item 1 de "Identificação do IP do cliente": o security group da EC2 aceita só o CloudFront, e essa restrição está em vigor, porque o [ADR-07](ADR-07-http-entre-cloudfront-e-api.md) também depende dela.

## Contexto

A API publicada é acessível pela internet. Sem limite de requisições, ela fica exposta a:

- tentativas repetidas de adivinhar senhas no login.
- criação de incidentes em massa, por erro (ex.: clique repetido) ou abuso.
- excesso de requisições que degradam o serviço para os demais usuários.

O limite pode ser contado por **IP** ou por **usuário**:

- **Analistas na central** costumam sair para a internet pelo mesmo IP corporativo. Um limite por IP seria dividido entre todos eles.
- **Motoristas em rede móvel** passam por CGNAT da operadora, então muitos celulares não relacionados compartilham poucos IPs.
- **Antes do login** não há usuário identificado, então o IP é a única informação disponível.

## Decisão

| Rota | Chave | Limite |
|---|---|---|
| Login | Nome de usuário informado | 5 tentativas/min |
| Login | IP | 20 tentativas/min |
| Criação de incidente | Usuário autenticado | 10/min |
| Demais rotas autenticadas | Usuário autenticado | 100/min |

- Ao exceder o limite, a API responde **HTTP 429 Too Many Requests** com o cabeçalho `Retry-After`.
- O frontend lê o `Retry-After` e exibe uma mensagem como "Muitas tentativas. Tente novamente em X segundos."
- Implementação com a biblioteca **slowapi**, com armazenamento em memória.

### Identificação do IP do cliente

A API fica atrás do CloudFront (ADR-01), então o endereço da conexão que chega à EC2 é o do CloudFront, não o do cliente. O cabeçalho `X-Forwarded-For` **não é confiável**: o cliente pode enviá-lo com qualquer valor, e o CloudFront apenas acrescenta o IP real ao final da lista, sem remover o que veio antes. Confiar nele permitiria trocar de "IP" a cada tentativa e contornar o limite por IP.

Para garantir que o IP usado no limite seja o real:

1. **Acesso à EC2 restrito ao CloudFront.** O Security Group da EC2 aceita tráfego HTTP apenas da *managed prefix list* `com.amazonaws.global.cloudfront.origin-facing`. Ninguém acessa a API diretamente pelo IP da instância.
2. **IP lido do cabeçalho `CloudFront-Viewer-Address`.** Esse cabeçalho é preenchido pelo próprio CloudFront com o IP do cliente e incluído na *origin request policy* do comportamento `/api/*`.

O uvicorn **não** é configurado com `--forwarded-allow-ips="*"`.

### Justificativa dos valores

- **Login, 5/min por usuário:** suficiente para quem errou a senha algumas vezes; impede tentativas em massa contra uma conta.
- **Login, 20/min por IP:** permite que vários analistas de uma central entrem ao mesmo tempo no início do turno, mas freia quem testa muitos usuários a partir do mesmo lugar.
- **Criação, 10/min:** nenhum motorista reporta 10 incidentes reais em um minuto.
- **Demais, 100/min:** cobre atualização periódica da lista, filtros e ações, com folga.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Somente por IP** | Penaliza usuários legítimos que compartilham IP. |
| **Somente por usuário** | Não protege o login, onde o usuário ainda não está autenticado. |
| **Rate limit na infraestrutura** (AWS WAF) | Mais robusto e aplicado antes de chegar à API, mas tem custo mensal fixo por regra e não enxerga o usuário autenticado, necessário para os limites por usuário. |
| **Armazenamento em Redis** | Necessário com várias instâncias da API. Com uma instância só, a memória basta. Maior Complexidade. |
| **Confiar no `X-Forwarded-For`** | O cliente controla o conteúdo do cabeçalho e pode falsificar o IP, anulando o limite por IP. |
| **Cabeçalho secreto entre CloudFront e API** | A prefix list libera qualquer distribuição CloudFront, inclusive uma criada por terceiros apontando para a EC2. Um cabeçalho secreto adicionado pelo CloudFront fecharia essa brecha, mas o risco é baixo para o MVP. Candidato a evolução. |

## Consequências

**Positivas**

- Proteção básica contra força bruta e abuso, testável com testes automatizados.
- Usuários legítimos que compartilham IP não se prejudicam nas rotas autenticadas.
- O IP usado no limite não pode ser falsificado pelo cliente.
- A EC2 não fica exposta diretamente à internet.

**Negativas**

- Contadores em memória são zerados quando a API reinicia e não são compartilhados entre instâncias. **Evolução:** usar Redis ao escalar horizontalmente.
- Valores definidos por estimativa, não por medição de uso real. Devem ser revistos com dados de produção.
- Sem o cabeçalho secreto, uma distribuição CloudFront de terceiros ainda consegue alcançar a EC2. **Evolução:** adicionar o cabeçalho secreto, com o valor guardado no SSM Parameter Store.
- A identificação do IP depende do CloudFront. Se a API for exposta por outro caminho, a função `client_ip` precisa ser revista.
