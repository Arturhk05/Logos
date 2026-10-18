# ADR-07: HTTP entre o CloudFront e a API

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

O CloudFront é o único ponto de entrada da aplicação (ADR-01): o navegador fala com ele em HTTPS, e ele encaminha `/api/*` para a API, que roda num container na EC2. Falta decidir como o CloudFront fala com a EC2.

Nesse trecho passam o cookie de sessão (ADR-03) e o corpo do login, com a senha. Quem conseguisse observar o tráfego entre o CloudFront e a EC2 poderia capturar sessões.

Para usar HTTPS nesse trecho, a EC2 precisaria de um certificado emitido por uma autoridade pública para o nome da origem: o CloudFront recusa certificados autoassinados, e o ACM não entrega certificados para instalar numa EC2.

## Decisão

O CloudFront fala com a EC2 em **HTTP, na porta 80**. O HTTPS termina no CloudFront.

Mitigações:

- **A EC2 só aceita conexões do CloudFront:** o security group libera a porta 80 apenas para a prefix list gerenciada `com.amazonaws.global.cloudfront.origin-facing` (ADR-04), e nenhuma outra porta fica aberta. Ninguém acessa a API sem passar pelo CloudFront.
- **O navegador nunca usa HTTP com a API:** o comportamento `/api/*` aceita apenas HTTPS. Requisições em HTTP são recusadas em vez de redirecionadas, porque um redirecionamento faria o navegador reenviar o login sem o corpo.
- O CloudFront e a EC2 estão na AWS, em `us-east-1`. O tráfego entre eles normalmente passa pela rede da própria AWS, mas isso **não é garantido** nem cifrado, e por isso não conta como mitigação.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| **Certificado Let's Encrypt na EC2** (nginx ou Caddy) | Sem custo, mas a emissão e as renovações (a cada 60 a 90 dias) exigem validação por HTTP, que precisaria abrir a porta 80 para a internet e desfaria o isolamento da EC2, ou validação por DNS, que depende de integração com a API de DNS da Hostinger. Exige também um nome próprio para a origem. Mais peças para manter no MVP. |
| **Load balancer (ALB) com certificado do ACM** | Solução gerenciada e sem renovação manual, mas custa cerca de US$ 18 por mês, uma parte grande dos créditos do projeto. |
| **CloudFront VPC origins** (EC2 em subnet privada) | O tráfego fica dentro da rede da AWS, mas a EC2 em subnet privada precisaria de NAT Gateway (cerca de US$ 32 por mês) ou de VPC endpoints para baixar as imagens do ECR. |

## Consequências

**Positivas**

- Nenhum certificado para emitir, renovar ou instalar na EC2.
- Nenhum custo adicional.
- A EC2 continua inacessível fora do CloudFront.

**Negativas**

- O cookie de sessão e a senha do login trafegam sem cifra entre o CloudFront e a EC2.
- O risco depende de alguém conseguir observar esse trecho da rede. É aceitável para uma demonstração, mas não para dados reais.

**Evolução:** para dados reais, cifrar até a origem com um ALB e um certificado do ACM, mudando o CloudFront para `https-only`, ou com um certificado público na própria EC2, renovado por validação de DNS.
