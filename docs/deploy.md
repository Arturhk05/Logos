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

## 2. Rede e banco

A VPC padrão tem só subnets públicas. O banco fica em duas subnets privadas novas (o RDS exige duas zonas de disponibilidade), com uma route table que só tem a rota local, ou seja, sem saída nem entrada pela internet. Não há NAT Gateway: o banco não precisa acessar a internet.

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)
tags() { echo "ResourceType=$1,Tags=[{Key=Name,Value=$2},{Key=Project,Value=logos}]"; }

SUBNET_A=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 172.31.96.0/20 --availability-zone us-east-1a \
  --tag-specifications "$(tags subnet logos-private-a)" --query Subnet.SubnetId --output text)
SUBNET_B=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 172.31.112.0/20 --availability-zone us-east-1b \
  --tag-specifications "$(tags subnet logos-private-b)" --query Subnet.SubnetId --output text)

RTB=$(aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications "$(tags route-table logos-private)" \
  --query RouteTable.RouteTableId --output text)
aws ec2 associate-route-table --route-table-id $RTB --subnet-id $SUBNET_A
aws ec2 associate-route-table --route-table-id $RTB --subnet-id $SUBNET_B
```

Security groups: o da EC2 nasce sem nenhuma entrada (a porta 80 para o CloudFront é liberada na etapa 3), e o do banco aceita a porta 5432 apenas a partir do security group da EC2.

```bash
SG_EC2=$(aws ec2 create-security-group --group-name logos-ec2 --description "Logos API host: HTTP only from CloudFront" \
  --vpc-id $VPC_ID --tag-specifications "$(tags security-group logos-ec2)" --query GroupId --output text)
SG_RDS=$(aws ec2 create-security-group --group-name logos-rds --description "Logos database: PostgreSQL only from the API host" \
  --vpc-id $VPC_ID --tag-specifications "$(tags security-group logos-rds)" --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_RDS --protocol tcp --port 5432 --source-group $SG_EC2
```

Banco PostgreSQL 18, sem acesso público, com disco criptografado e proteção contra exclusão. A senha é lida do SSM dentro do próprio comando.

> Contas no plano gratuito da AWS aceitam no máximo 1 dia de retenção de backup (`FreeTierRestrictionError` com valores maiores).

```bash
aws rds create-db-subnet-group --db-subnet-group-name logos-db-subnets --db-subnet-group-description "Logos private subnets" \
  --subnet-ids $SUBNET_A $SUBNET_B --tags Key=Project,Value=logos

aws rds create-db-instance \
  --db-instance-identifier logos-db \
  --engine postgres --engine-version 18.6 --auto-minor-version-upgrade \
  --db-instance-class db.t4g.micro --no-multi-az \
  --storage-type gp3 --allocated-storage 20 --storage-encrypted \
  --db-name logos --master-username logos \
  --master-user-password "$(aws ssm get-parameter --name /logos/db-password --with-decryption --query Parameter.Value --output text)" \
  --db-subnet-group-name logos-db-subnets --vpc-security-group-ids $SG_RDS --no-publicly-accessible \
  --backup-retention-period 1 --copy-tags-to-snapshot --deletion-protection \
  --tags Key=Project,Value=logos

aws rds wait db-instance-available --db-instance-identifier logos-db
```

URL de conexão da API, montada a partir do endpoint e da senha e gravada no SSM, também sem aparecer no terminal. O `sslmode=require` obriga a conexão cifrada até o RDS.

```bash
DB_HOST=$(aws rds describe-db-instances --db-instance-identifier logos-db --query 'DBInstances[0].Endpoint.Address' --output text)
aws ssm put-parameter --name /logos/database-url --type SecureString --tags Key=Project,Value=logos \
  --value "postgresql+psycopg://logos:$(aws ssm get-parameter --name /logos/db-password --with-decryption --query Parameter.Value --output text)@$DB_HOST:5432/logos?sslmode=require"
```

Verificação: o banco não pode ter endpoint público.

```bash
aws rds describe-db-instances --db-instance-identifier logos-db \
  --query 'DBInstances[0].[DBInstanceStatus,PubliclyAccessible,DBSubnetGroup.Subnets[].SubnetIdentifier]'
```
