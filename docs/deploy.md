# Deploy na AWS

Runbook da infraestrutura do Logos na AWS (ADR-01): os comandos na ordem em que foram executados, para recriar o ambiente do zero ou removê-lo ao fim da avaliação.

## Visão geral

```
                 ┌──────────────── CloudFront (HTTPS) ────────────────┐
 usuário ──────► │  /*      → S3 (build do React)                     │
                 │  /api/*  → EC2 (container FastAPI)                 │
                 └────────────────────────────────────────────────────┘
                                         │
                                         ▼
                           RDS PostgreSQL (subnet privada)
```

- Região: `us-east-1`.
- Todos os recursos têm o prefixo `logos-` e a tag `Project=logos`.
- Os arquivos usados pelos comandos (políticas, configurações) ficam em [`infra/`](../infra).
- Segredos (segredo do JWT, senha do banco) ficam no SSM Parameter Store e **nunca** são exibidos no terminal.

## Pré-requisitos

1. MFA ativado na conta root, e acesso dos usuários IAM às informações de cobrança ativado (**Account → IAM user and role access to Billing information**).
2. Usuário IAM `logos-admin`, com `AdministratorAccess`, MFA no console e uma access key para o CLI. **Apague a access key ao fim da avaliação.**
3. [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configurado com o perfil `logos`:

   ```bash
   aws configure --profile logos   # região us-east-1, saída json
   aws sts get-caller-identity --profile logos
   ```

Variáveis usadas nos comandos abaixo (bash):

```bash
export AWS_PROFILE=logos AWS_REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export MSYS_NO_PATHCONV=1   # só no Git Bash do Windows: impede que "/logos/..." vire um caminho do Windows
```

## 1. Orçamento, registro de imagens e segredos

Orçamento mensal de US$ 30, com alerta por e-mail quando o gasto real passar de 80% e quando a previsão do mês passar de 100%:

```bash
EMAIL="<seu e-mail>"
aws budgets create-budget --account-id "$ACCOUNT_ID" --budget file://infra/budget.json \
  --notifications-with-subscribers "[
    {\"Notification\":{\"NotificationType\":\"ACTUAL\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":80,\"ThresholdType\":\"PERCENTAGE\"},\"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$EMAIL\"}]},
    {\"Notification\":{\"NotificationType\":\"FORECASTED\",\"ComparisonOperator\":\"GREATER_THAN\",\"Threshold\":100,\"ThresholdType\":\"PERCENTAGE\"},\"Subscribers\":[{\"SubscriptionType\":\"EMAIL\",\"Address\":\"$EMAIL\"}]}
  ]"
```

Repositório de imagens da API, com verificação de vulnerabilidades no envio e apenas as 10 imagens mais recentes:

```bash
aws ecr create-repository --repository-name logos-api \
  --image-scanning-configuration scanOnPush=true --tags Key=Project,Value=logos
aws ecr put-lifecycle-policy --repository-name logos-api \
  --lifecycle-policy-text file://infra/ecr-lifecycle-policy.json
```

Segredo do JWT e senha do banco, gerados e gravados direto no SSM, sem aparecer no terminal. O `token_urlsafe` só usa letras, números, `-` e `_`: caracteres aceitos pelo RDS na senha mestra e que não precisam de escape na URL do banco.

```bash
for name in jwt-secret db-password; do
  aws ssm put-parameter --name "/logos/$name" --type SecureString \
    --value "$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
    --tags Key=Project,Value=logos --query Version --output text
done
```
