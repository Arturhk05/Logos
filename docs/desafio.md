## **O Desafio (Contexto)**

A AutoU foi contratada por um gigante da logística para **digitalizar sua "Central de Resposta a Incidentes".** Hoje, o cliente opera no escuro: a comunicação entre os 5.000 caminhões em rota e a central de decisão é um caos de WhatsApp e planilhas manuais que não se conversam. Eles perdem milhões de reais anualmente porque levam horas para reagir a um simples pneu furado ou a um bloqueio de estrada.

Sua missão é construir o **MVP do "Logos"** - a plataforma que será o cérebro dessa operação, definida para você como **uma ferramenta de missão crítica.**

## Objetivo do Desafio Simplificado

Os analistas do cliente trabalham sob altíssima pressão; para resolver o problema, eles precisam de uma interface que **organize o caos**. O sistema deve ser capaz de:

- **Ingestão e Visualização de Dados:** Criar uma API robusta que receba e sirva incidentes (que são categorizados por: Acidente com Veículo, Acidente com Vítimas, Condição Climática Atípica na Pista , Problema Mecânico, Bloqueio de Pista). No Front-end, como você apresenta 100 incidentes simultâneos garantindo que o analista identifique o que é prioridade em milissegundos?
- **Gestão por Exceção:** O sistema deve permitir filtrar por criticidade (que pode ser Alta, Média, Baixa) e as categorias.
- **Integridade no Ciclo de Vida:** Ao interagir com os dados para mudar um status (ex: de "Aberto" para "Em Investigação"), como sua aplicação garante que dois analistas não tentem resolver o mesmo problema ao mesmo tempo? Considere os seguintes status:
    - Aberto;
    - Fechado;
    - Em Investigação;
    - Inconclusivo.
- **Resiliência e Performance:** O cliente espera que o sistema seja rápido e não "quebre" se a conexão oscilar. Como seu código trata o estado da aplicação enquanto o banco de dados processa uma atualização?

## Entregáveis

#### **1. Repositório de Código (Backend + Frontend)**

Formato: Link **público** do GitHub ou GitLab.

Este é o coração da sua entrega. Esperamos uma estrutura de pastas organizada e profissional.

- Uma API funcional (Python) que gerencie o CRUD dos incidentes e persista os dados (DB ou JSON estruturado).
- Uma interface (React) que consuma essa API com sucesso.
- Instruções claras de setup e uma breve explicação das escolhas de arquitetura e bibliotecas utilizadas.

> *Obs*: Organize o repositório com atenção à estrutura e à clareza de leitura.
> 

#### **2. Vídeo de Demonstração Técnica**

Formato: Link **público** (YouTube ou Drive) - Até 5 minutos.

Faça um "code review" da sua própria solução e uma demo das funcionalidades:

- Mostre a integração entre Front e Back.
- Demonstre o tratamento de estados (loading, erro, empty state).
- Explique como você estruturou a lógica de filtros e a segurança básica da API.

> *Obs*: Garanta que seu vídeo está publicado e com acesso liberado para que qualquer um com o link possa assistir.
> 

#### **3. Link da Solução Deployada na Nuvem**

Forneça um **link funcional** para que possamos acessar e testar sua aplicação diretamente em um **ambiente online** (por exemplo: Vercel, Render, Hugging Face Spaces, Replit, Heroku, GCP, Azure, AWS, etc).

A aplicação deve estar pronta para uso, sem necessidade de instalação local. Caso haja autenticação ou instruções específicas para uso, inclua essa orientação na tela inicial ou no próprio README enviado no Github.

A interface deve ser simples, intuitiva e com uma navegação amigável, mesmo para usuários não técnicos. Recomendamos que o foco esteja em:

- **Facilidade de uso** (sem dependência de instruções externas);
- **Clareza na experiência** (mostrar o propósito da aplicação de forma direta);
- **Organização visual** (sem excesso de elementos ou distrações desnecessárias).

Caso opte por não hospedar a aplicação, justifique brevemente o motivo no campo de entrega, e certifique-se de que o repositório contenha todos os arquivos necessários para rodar localmente, com instruções claras.

## Critérios de Avaliação

1. Arquitetura, Qualidade e Boas Práticas de Código

- **Histórico de Versionamento:** Tenha em mente que um histórico composto por um único *commit* ou com mensagens genéricas não demonstra o seu processo de construção.
- **Organização e Modularização:** Estruture suas pastas de forma lógica.
- **Clareza e Autenticidade:** Utilize uma nomenclatura de variáveis clara e profissional.
- **Documentação:** Explique claramente as instruções de setup e justifique as decisões técnicas e de arquitetura que você tomou.

2. Frontend, UX e Design 

- **Feedback Visual:** O usuário nunca deve ficar na dúvida se o sistema travou ou está processando.
- **Atenção aos Detalhes:** Avaliaremos o seu cuidado com espaçamentos, tipografia, e interações.
- **Diferenciais de Usabilidade:** Implementações como um Modo Claro/Escuro funcional e transições fluidas entre as telas somam muitos pontos a seu favor.
- **Design da Informação:** Lembre-se de que o analista precisa bater o olho em 100 incidentes e priorizá-los em milissegundos - pense em como o design vai facilitar essa gestão por exceção.

3. Backend, Lógica e Resiliência 

- **Robustez e Validação:** Faça validações consistentes nas entradas de dados e garanta que a aplicação não "quebre" caso receba informações inesperadas.
- **Integridade de Dados:** Estruture a sua lógica para garantir que, se dois analistas tentarem editar o *status* do mesmo incidente ao mesmo tempo, o sistema saiba tratar esse conflito sem corromper a operação.
- **Tratamento de Exceções de Rede:** Demonstre um pensamento escalável garantindo que seu código saiba lidar graciosamente com falhas temporárias ou lentidão no banco de dados.

## Instruções de Entrega

A entrega deve ser feita **exclusivamente** através da página do candidato em nossa plataforma de recrutamento.

Nessa página, você irá colar os seguintes links:

- Link público do repositório no GitHub com o código-fonte do projeto e outras informações úteis.
- Link público do vídeo de apresentação rápida do projeto (ex: YouTube).
- Link da aplicação publicada (ex: Render, Hugging Face Spaces, Replit, Heroku, GCP, AWS, Azure ou similar).

*Reminders* para a entrega:

1. Certifique-se de que todos os **links estejam acessíveis publicamente** e que não exijam permissões especiais.
2. O **envio deve ser feito até a data limite informada no e-mail** de confirmação. Envios após o prazo não serão considerados.
3. O envio do case deve ser feito **exclusivamente pelo formulário** acima. **Não serão aceitos arquivos ou links enviados por e-mail, WhatsApp ou qualquer outro canal.** Toda a análise será feita apenas com base nas informações preenchidas no formulário.

## Considerações finais

**Minha principal dica para você é:**

Enxergar este case como uma grande oportunidade de aplicar seus conhecimentos na criação de algo prático e se desenvolver profissionalmente. 

Foque em realmente entender o desafio, o contexto do problema e em criar uma solução digital que resolva e melhore a vida do usuário. Não existe resposta certa ou errada, nem gabarito. 

**Capriche bastante na sua solução, estamos ansiosos para ver o que você irá criar, boa sorte!** 🚀