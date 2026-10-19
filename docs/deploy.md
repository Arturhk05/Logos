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

As seções seguintes reaproveitam variáveis criadas nas anteriores. Para continuar em um terminal novo, recupere as que já existem:

```bash
VPC_ID=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true --query 'Vpcs[0].VpcId' --output text)
SG_EC2=$(aws ec2 describe-security-groups --filters Name=group-name,Values=logos-ec2 --query 'SecurityGroups[0].GroupId' --output text)
SG_RDS=$(aws ec2 describe-security-groups --filters Name=group-name,Values=logos-rds --query 'SecurityGroups[0].GroupId' --output text)
INSTANCE_ID=$(aws ec2 describe-instances --filters Name=tag:Name,Values=logos-api Name=instance-state-name,Values=running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
tags() { echo "ResourceType=$1,Tags=[{Key=Name,Value=$2},{Key=Project,Value=logos}]"; }
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

## 3. Servidor da API (EC2)

Papel da instância, só com políticas gerenciadas pela AWS:

- `AmazonSSMManagedInstanceCore`: acesso pelo SSM (Session Manager e Run Command, sem SSH). Essa política também permite ler os parâmetros do SSM, que é como a instância obtém os segredos no deploy. Ela não restringe quais parâmetros podem ser lidos, o que é aceitável numa conta que só tem os parâmetros `/logos/*`.
- `AmazonEC2ContainerRegistryPullOnly`: apenas baixar imagens do ECR.

```bash
aws iam create-role --role-name logos-ec2-role --assume-role-policy-document file://infra/ec2-trust-policy.json \
  --tags Key=Project,Value=logos
aws iam attach-role-policy --role-name logos-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam attach-role-policy --role-name logos-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly
aws iam create-instance-profile --instance-profile-name logos-ec2-profile --tags Key=Project,Value=logos
aws iam add-role-to-instance-profile --instance-profile-name logos-ec2-profile --role-name logos-ec2-role
```

A porta 80 da EC2 aceita conexões apenas dos servidores de origem do CloudFront, pela prefix list gerenciada pela AWS (ADR-04). Nenhuma outra porta fica aberta.

```bash
PREFIX_LIST=$(aws ec2 describe-managed-prefix-lists \
  --filters Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing \
  --query 'PrefixLists[0].PrefixListId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_EC2 \
  --ip-permissions "IpProtocol=tcp,FromPort=80,ToPort=80,PrefixListIds=[{PrefixListId=$PREFIX_LIST,Description=\"CloudFront origin-facing\"}]"
```

Instância ARM (`t4g.micro`) com Amazon Linux 2023, na subnet pública da mesma zona do RDS (sem custo de tráfego entre zonas). Não tem key pair: o acesso é só pelo Session Manager. O IMDSv2 é obrigatório, e os containers não alcançam o serviço de metadados (`HttpPutResponseHopLimit=1`). O [`ec2-user-data.sh`](../infra/ec2-user-data.sh) instala o Docker no primeiro boot.

> Logo depois de criado, o instance profile pode levar alguns segundos para ser reconhecido (`Invalid IAM Instance Profile`). Basta repetir o comando.

```bash
DB_AZ=$(aws rds describe-db-instances --db-instance-identifier logos-db --query 'DBInstances[0].AvailabilityZone' --output text)
PUBLIC_SUBNET=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID Name=availability-zone,Values=$DB_AZ Name=default-for-az,Values=true \
  --query 'Subnets[0].SubnetId' --output text)
AMI_ID=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query Parameter.Value --output text)

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID --instance-type t4g.micro \
  --subnet-id $PUBLIC_SUBNET --security-group-ids $SG_EC2 \
  --iam-instance-profile Name=logos-ec2-profile \
  --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1,HttpEndpoint=enabled \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=20,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}' \
  --user-data file://infra/ec2-user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=logos-api},{Key=Project,Value=logos}]' \
                       'ResourceType=volume,Tags=[{Key=Name,Value=logos-api},{Key=Project,Value=logos}]' \
  --query 'Instances[0].InstanceId' --output text)
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Proteção contra encerramento: a instância não pode ser apagada por engano (desligar antes de remover tudo).
aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --disable-api-termination
```

Elastic IP: um endereço fixo para a instância. Sem ele, o IP público muda toda vez que a instância é parada e iniciada, e a origem do CloudFront deixaria de funcionar.

```bash
ALLOCATION_ID=$(aws ec2 allocate-address --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=logos-api},{Key=Project,Value=logos}]' \
  --query AllocationId --output text)
aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $ALLOCATION_ID
```

Verificação: a instância aparece `Online` no SSM (1 a 3 minutos depois do boot), o Docker responde e os segredos podem ser lidos (o segundo comando mostra só o tamanho do valor, nunca o conteúdo).

```bash
aws ssm describe-instance-information --filters Key=InstanceIds,Values=$INSTANCE_ID --query 'InstanceInformationList[0].PingStatus'

run_on_instance() {
  local cmd
  cmd=$(aws ssm send-command --instance-ids $INSTANCE_ID --document-name AWS-RunShellScript \
    --parameters "commands=[\"$1\"]" --query Command.CommandId --output text)
  aws ssm wait command-executed --command-id $cmd --instance-id $INSTANCE_ID
  aws ssm get-command-invocation --command-id $cmd --instance-id $INSTANCE_ID --query StandardOutputContent --output text
}
run_on_instance "cloud-init status --wait >/dev/null; docker --version"
run_on_instance "aws ssm get-parameter --region us-east-1 --name /logos/jwt-secret --with-decryption --query 'length(Parameter.Value)' --output text"
```

Para abrir um terminal na instância, sem SSH (requer o [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)):

```bash
aws ssm start-session --target $INSTANCE_ID
```

## 4. Deploy automático (GitHub Actions)

A cada push na `main` que altere `backend/`, o [`deploy-backend.yml`](../.github/workflows/deploy-backend.yml) faz:

1. **test**: ruff, mypy e pytest. Nada sobe se algum falhar.
2. **build**: constrói a imagem num runner ARM do GitHub (a EC2 é ARM, então não há emulação) e envia ao ECR com a tag do commit.
3. **deploy**: envia o [`ec2-deploy.sh`](../infra/ec2-deploy.sh) para a EC2 pelo SSM Run Command e espera o resultado. O script monta o `.env` a partir do SSM, roda migrations e seed num container avulso e só então troca o container da API. Se as migrations falharem, a versão anterior continua no ar.

O GitHub não guarda nenhuma chave da AWS: o workflow se autentica por OIDC e assume o papel `logos-github-deploy`, que só aceita a branch `main` deste repositório e só pode enviar imagens ao `logos-api` e comandos à instância da API.

```bash
aws iam create-open-id-connect-provider --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com --tags Key=Project,Value=logos

fill() { sed -e "s/ACCOUNT_ID/$ACCOUNT_ID/g" -e "s/INSTANCE_ID/$INSTANCE_ID/g" "$1"; }
aws iam create-role --role-name logos-github-deploy --max-session-duration 3600 --tags Key=Project,Value=logos \
  --assume-role-policy-document "$(fill infra/github-oidc-trust-policy.json)"
aws iam put-role-policy --role-name logos-github-deploy --policy-name logos-deploy \
  --policy-document "$(fill infra/github-deploy-policy.json)"
```

O workflow lê o ID da conta e o da instância de **variables** do repositório (não são segredos):

```bash
gh variable set AWS_ACCOUNT_ID --body "$ACCOUNT_ID"
gh variable set EC2_INSTANCE_ID --body "$INSTANCE_ID"
```

Para fazer um deploy sem novo commit (por exemplo, depois de trocar um segredo no SSM):

```bash
gh workflow run deploy-backend.yml
gh run watch
```

> Com uma instância só, a API fica alguns segundos indisponível durante a troca de containers. Também não há volta automática: se a versão nova não ficar saudável, a API fica fora do ar até um novo deploy. Para voltar, reverta o commit na `main` e faça push (o papel de deploy só aceita a branch `main`).

## 5. Domínio, HTTPS e CloudFront

Certificado do ACM para o domínio, validado por DNS. O ACM informa um registro `CNAME` que precisa ser criado no provedor DNS do domínio (Hostinger) e **mantido**: ele também é usado nas renovações automáticas.

```bash
CERT_ARN=$(aws acm request-certificate --domain-name logos.arturkrauspenhar.com.br --validation-method DNS \
  --tags Key=Project,Value=logos --query CertificateArn --output text)
aws acm describe-certificate --certificate-arn $CERT_ARN \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord'   # criar este CNAME na Hostinger
aws acm wait certificate-validated --certificate-arn $CERT_ARN
```

> Na Hostinger, o campo **Nome** recebe só a parte antes do domínio (por exemplo, `_03a6....logos`), e o destino vai sem o ponto final.

Bucket privado para o frontend (por enquanto, só a [página provisória](../infra/frontend-placeholder/index.html)), acessível apenas pelo CloudFront via OAC:

```bash
BUCKET=logos-frontend-$ACCOUNT_ID
aws s3api create-bucket --bucket $BUCKET
aws s3api put-public-access-block --bucket $BUCKET \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-tagging --bucket $BUCKET --tagging 'TagSet=[{Key=Project,Value=logos}]'
aws s3 cp infra/frontend-placeholder/index.html s3://$BUCKET/index.html --content-type "text/html; charset=utf-8" --cache-control no-cache

OAC_ID=$(aws cloudfront create-origin-access-control --origin-access-control-config \
  'Name=logos-frontend-oac,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3' \
  --query OriginAccessControl.Id --output text)
```

Função do CloudFront que entrega o `index.html` nas rotas do React, como `/fila/123` ([ADR-09](adr/ADR-09-rotas-do-frontend-no-cloudfront.md), [código](../infra/cloudfront-spa-routes.js)). Ela nasce no estágio `DEVELOPMENT`, é testada e só então publicada:

```bash
aws cloudfront create-function --name logos-spa-routes \
  --function-config 'Comment=Logos: serve index.html for React routes (ADR-09),Runtime=cloudfront-js-2.0' \
  --function-code fileb://infra/cloudfront-spa-routes.js
FUNCTION_ARN=arn:aws:cloudfront::$ACCOUNT_ID:function/logos-spa-routes
aws cloudfront tag-resource --resource $FUNCTION_ARN --tags 'Items=[{Key=Project,Value=logos}]'

# Rotas viram /index.html; arquivos (com ponto no último trecho) mantêm o caminho; a query string não muda.
ETAG=$(aws cloudfront describe-function --name logos-spa-routes --stage DEVELOPMENT --query ETag --output text)
for uri in / /fila/123 /meus-reportes /index.html /assets/index-abc.js; do
  printf '{"version":"1.0","context":{"eventType":"viewer-request"},"viewer":{"ip":"198.51.100.1"},"request":{"method":"GET","uri":"%s","querystring":{},"headers":{},"cookies":{}}}' "$uri" > event.json
  echo "$uri -> $(aws cloudfront test-function --name logos-spa-routes --if-match $ETAG --stage DEVELOPMENT \
    --event-object fileb://event.json --query TestResult.FunctionOutput --output text)"
done
rm event.json

aws cloudfront publish-function --name logos-spa-routes \
  --if-match $(aws cloudfront describe-function --name logos-spa-routes --query ETag --output text)
```

Distribuição do CloudFront ([configuração](../infra/cloudfront-distribution.json)):

| Rota | Origem | Configuração |
|---|---|---|
| `/*` | S3, via OAC | cache `CachingOptimized`; HTTP é redirecionado para HTTPS; a função `logos-spa-routes` troca as rotas do React por `/index.html` |
| `/api/*` | EC2 (DNS do Elastic IP), porta 80 | sem cache (`CachingDisabled`), repassa cookies e cabeçalhos (`AllViewerExceptHostHeader`), todos os métodos, **só HTTPS** (um redirecionamento perderia o corpo de um `POST`) |

```bash
API_ORIGIN=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicDnsName' --output text)
config=$(sed -e "s|CALLER_REFERENCE|logos-$(date +%Y%m%d%H%M%S)|" -e "s|BUCKET|$BUCKET|" -e "s|OAC_ID|$OAC_ID|" \
  -e "s|API_ORIGIN|$API_ORIGIN|" -e "s|CERTIFICATE_ARN|$CERT_ARN|" -e "s|FUNCTION_ARN|$FUNCTION_ARN|" \
  infra/cloudfront-distribution.json)
DISTRIBUTION_ID=$(aws cloudfront create-distribution-with-tags --distribution-config-with-tags "$config" \
  --query Distribution.Id --output text)

policy=$(sed -e "s|BUCKET|$BUCKET|" -e "s|ACCOUNT_ID|$ACCOUNT_ID|" -e "s|DISTRIBUTION_ID|$DISTRIBUTION_ID|" infra/s3-oac-bucket-policy.json)
aws s3api put-bucket-policy --bucket $BUCKET --policy "$policy"

aws cloudfront wait distribution-deployed --id $DISTRIBUTION_ID
aws cloudfront get-distribution --id $DISTRIBUTION_ID --query Distribution.DomainName --output text
```

Por fim, no provedor DNS: `CNAME` de `logos` para o domínio `*.cloudfront.net` da distribuição.

> No ambiente atual, a função foi criada depois da distribuição e associada a ela com `get-distribution-config`, acrescentando o `FunctionAssociations` ao `DefaultCacheBehavior`, e `update-distribution` (o mesmo procedimento de "Remover tudo"). O comportamento `/api/*` não tem função: as respostas da API, inclusive 401, 403 e 404, chegam ao navegador como saíram dela.

> **Trecho sem criptografia ([ADR-07](adr/ADR-07-http-entre-cloudfront-e-api.md)):** o HTTPS termina no CloudFront, e o CloudFront fala com a EC2 em HTTP. Esse trecho leva o cookie de sessão e o corpo do login sem cifra. A EC2 só aceita conexões do CloudFront, e os dois estão em `us-east-1`, mas o tráfego entre eles não é cifrado. É uma decisão consciente para o MVP: cifrar até a origem exigiria um certificado público na EC2 (Let's Encrypt, com validação que esbarra no isolamento da porta 80) ou um load balancer com certificado do ACM (cerca de US$ 18/mês).

## 6. Verificação

```bash
D=https://logos.arturkrauspenhar.com.br
curl -i $D/api/health                                   # 200 {"status":"ok"}
curl -i -c cookies.txt -X POST $D/api/auth/login -H "Content-Type: application/json" \
  -d '{"username":"camila","password":"logos123"}'      # 200 e Set-Cookie: HttpOnly; Secure; SameSite=strict; Path=/api; Max-Age=28800
curl -b cookies.txt $D/api/me                           # 200: o cookie passou pelo CloudFront até a API
curl -i $D/api/me                                       # 401 sem o cookie
curl -i http://logos.arturkrauspenhar.com.br/           # 301 para HTTPS
curl -i http://logos.arturkrauspenhar.com.br/api/health # 403: a API só aceita HTTPS
curl --max-time 5 http://<elastic-ip>/api/health        # timeout: a EC2 só aceita o CloudFront
rm cookies.txt

# Rotas do React (ADR-09)
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" $D/fila/123              # 200 text/html: index.html
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" $D/assets/nao-existe.js  # 403 application/xml: arquivo inexistente não vira HTML
curl -s -w " %{http_code}\n" $D/api/rota-que-nao-existe                         # 404 em JSON: a função não atua na API
curl -s -w " %{http_code}\n" $D/api/me                                          # 401 em JSON
```

No navegador, em `$D/api/docs`, fazer o login pelo Swagger (`POST /api/auth/login`) e depois chamar `GET /api/me`, que deve responder 200 sem nenhuma configuração extra.

## Remover tudo

Ao fim da avaliação, na ordem abaixo (cada recurso depende dos seguintes). Antes, recupere as variáveis do início deste documento.

```bash
# 1. CloudFront: desativar, esperar, apagar; depois a função, o OAC, o bucket e o certificado
DISTRIBUTION_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[0]=='logos.arturkrauspenhar.com.br'].Id" --output text)
aws cloudfront get-distribution-config --id $DISTRIBUTION_ID > dist.json
ETAG=$(python -c "import json; print(json.load(open('dist.json'))['ETag'])")
python -c "import json; d=json.load(open('dist.json'))['DistributionConfig']; d['Enabled']=False; json.dump(d, open('dist-config.json','w'))"
aws cloudfront update-distribution --id $DISTRIBUTION_ID --if-match $ETAG --distribution-config file://dist-config.json
aws cloudfront wait distribution-deployed --id $DISTRIBUTION_ID
aws cloudfront delete-distribution --id $DISTRIBUTION_ID \
  --if-match $(aws cloudfront get-distribution --id $DISTRIBUTION_ID --query ETag --output text)
rm dist.json dist-config.json
aws cloudfront delete-function --name logos-spa-routes \
  --if-match $(aws cloudfront describe-function --name logos-spa-routes --query ETag --output text)
OAC_ID=$(aws cloudfront list-origin-access-controls --query "OriginAccessControlList.Items[?Name=='logos-frontend-oac'].Id" --output text)
aws cloudfront delete-origin-access-control --id $OAC_ID \
  --if-match $(aws cloudfront get-origin-access-control --id $OAC_ID --query ETag --output text)
aws s3 rb s3://logos-frontend-$ACCOUNT_ID --force
aws acm delete-certificate --certificate-arn $(aws acm list-certificates \
  --query "CertificateSummaryList[?DomainName=='logos.arturkrauspenhar.com.br'].CertificateArn" --output text)
# Na Hostinger: apagar o CNAME "logos" e o de validação do ACM.

# 2. Deploy automático
gh variable delete AWS_ACCOUNT_ID && gh variable delete EC2_INSTANCE_ID
aws iam delete-role-policy --role-name logos-github-deploy --policy-name logos-deploy
aws iam delete-role --role-name logos-github-deploy
aws iam delete-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::$ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com

# 3. EC2 (desligando antes a proteção contra encerramento), Elastic IP e papel da instância
aws ec2 modify-instance-attribute --instance-id $INSTANCE_ID --no-disable-api-termination
aws ec2 terminate-instances --instance-ids $INSTANCE_ID
aws ec2 wait instance-terminated --instance-ids $INSTANCE_ID
aws ec2 release-address --allocation-id $(aws ec2 describe-addresses \
  --filters Name=tag:Project,Values=logos --query 'Addresses[0].AllocationId' --output text)
aws iam remove-role-from-instance-profile --instance-profile-name logos-ec2-profile --role-name logos-ec2-role
aws iam delete-instance-profile --instance-profile-name logos-ec2-profile
aws iam detach-role-policy --role-name logos-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
aws iam detach-role-policy --role-name logos-ec2-role --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPullOnly
aws iam delete-role --role-name logos-ec2-role

# 4. Banco (desligando antes a proteção contra exclusão; sem snapshot final, que teria custo de armazenamento)
aws rds modify-db-instance --db-instance-identifier logos-db --no-deletion-protection --apply-immediately
aws rds delete-db-instance --db-instance-identifier logos-db --skip-final-snapshot --delete-automated-backups
aws rds wait db-instance-deleted --db-instance-identifier logos-db
aws rds delete-db-subnet-group --db-subnet-group-name logos-db-subnets

# 5. Rede: security groups (o do banco referencia o da EC2), subnets privadas e route table
aws ec2 delete-security-group --group-id $SG_RDS
aws ec2 delete-security-group --group-id $SG_EC2
for subnet in $(aws ec2 describe-subnets --filters Name=tag:Project,Values=logos --query 'Subnets[].SubnetId' --output text); do
  aws ec2 delete-subnet --subnet-id $subnet
done
aws ec2 delete-route-table --route-table-id $(aws ec2 describe-route-tables \
  --filters Name=tag:Name,Values=logos-private --query 'RouteTables[0].RouteTableId' --output text)

# 6. Segredos, imagens e orçamento
aws ssm delete-parameters --names /logos/jwt-secret /logos/db-password /logos/database-url
aws ecr delete-repository --repository-name logos-api --force
aws budgets delete-budget --account-id $ACCOUNT_ID --budget-name logos-monthly
```

Por último, no console: apagar a access key do usuário `logos-admin` (ou o próprio usuário) e conferir no **Tag Editor**, com a tag `Project=logos`, que não sobrou nenhum recurso.
