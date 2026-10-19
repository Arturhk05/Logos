# Requisitos

Os requisitos foram escritos em forma de histórias de usuário, a fim de facilitar a compreensão do valor que cada funcionalidade traz para o usuário final.

## Sumário

- [Personas](#personas)
- [Regras de negócio](#regras-de-negócio)
- [Histórias de usuário](#histórias-de-usuário)
- [Requisitos não funcionais](#requisitos-não-funcionais)

## Personas

| Persona                                                 | Papel                   | Interage via           |
| ------------------------------------------------------- | ----------------------- | ---------------------- |
| [Camila](#p1---camila-analista-da-central)              | Analista da Central     | Interface web          |
| [Roberto](#p2---roberto-supervisor-de-operações)        | Supervisor de Operações | Interface web          |
| [José](#p3---josé-motorista)                            | Motorista               | Interface web (mobile) |

### P1 - Camila, Analista da Central

_"Quando chega um acidente com vítima, eu não posso perder 10 minutos rolando o WhatsApp para descobrir onde ele está."_

**Perfil**

- 27 anos, ensino superior em Logística.
- 3 anos na central de incidentes.
- Trabalha em turnos de 8 horas, em escala que inclui noites e fins de semana.
- Proficiência digital: média. Usa bem sistemas web e excel, mas não é da área de tecnologia.

**Contexto**

- Passa o turno inteiro com WhatsApp e planilhas abertas em um monitor grande.
- Divide a fila de incidentes com outros analistas no mesmo turno.
- Recebe dezenas de ocorrências por hora, pode ter picos em dias de chuva.

**Objetivos**

- Identificar em segundos quais incidentes são críticos.
- Assumir um incidente e ter certeza de que ninguém mais está trabalhando nele.
- Registrar o andamento de cada ocorrência até o fechamento.

**Frustrações**

- Informações espalhadas entre grupos de WhatsApp e planilhas que não se conversam.
- Descobrir que outro analista já estava tratando o mesmo caso só depois de ligar para o motorista.

### P2 - Roberto, Supervisor de Operações

_"Quero ter visão geral de todos os incidentes e poder encerrar ou devolver à fila qualquer um deles."_

**Perfil**

- 41 anos, 15 anos no setor de transportes, começou como motorista e virou analista antes de assumir a supervisão.
- Lidera a equipe de analistas do turno.
- Proficiência digital: média.

**Contexto**

- Acompanha a fila geral de incidentes durante todo o turno.
- Intervém quando um incidente fica parado ou quando um analista sai do turno.

**Objetivos**

- Ter visão geral de tudo o que está aberto e em investigação.
- Encerrar ou devolver à fila incidentes de qualquer analista, para que outro possa assumi-los.
- Ter registro de quem fechou cada incidente e por qual motivo.

**Frustrações**

- Incidentes "órfãos" que ficam abertos porque o responsável saiu do turno.
- Não saber quem alterou um incidente, nem por quê.

### P3 - José, Motorista

_"Quando o meu pneu fura na estrada, eu quero reportar o incidente e acionar a central da empresa."_

**Perfil**

- 48 anos, motorista de caminhão há 20 anos.
- Passa a maior parte da semana em rota, muitas vezes em áreas com sinal de celular instável.
- Proficiência digital: baixa. Usa WhatsApp e pouco mais que isso.

**Contexto**

- Acessa o Logos pelo celular, parado no acostamento ou em um posto.
- Usa a tela apenas para reportar incidentes e acompanhar o que já reportou.
- Conexão instável: a requisição pode demorar ou falhar no meio do envio.

**Objetivos**

- Reportar um incidente de forma rápida e simples, sem estresse.
- Ter a garantia de que o reporte chegou à central.
- Saber se alguém da central já está cuidando do problema.

**Frustrações**

- Mandar mensagem em grupo e não ter certeza se alguém leu.
- Ter que explicar a mesma situação várias vezes, para pessoas diferentes.
- Formulários longos, com letras pequenas e campos difíceis de preencher no celular.

---

## Regras de negócio

- **RN-01** Incidentes são ordenados por criticidade (Mais crítica -> Menos crítica) e, dentro da mesma criticidade, do mais antigo para o mais recente.

- **RN-02:** Apenas incidentes com status _Aberto_ e sem responsável podem ser assumidos. Ao assumir, o status passa a _Em Investigação_. Assumir é a única forma de um incidente sair de _Aberto_, inclusive para o supervisor, que passa a ser o responsável.

- **RN-03:** Apenas o responsável pelo incidente ou um supervisor pode alterar seu status.

- **RN-04:** Transições de status permitidas:

  | De              | Para                          |
  | --------------- | ----------------------------- |
  | Aberto          | Em Investigação (ao assumir)  |
  | Em Investigação | Fechado, Inconclusivo, Aberto |
  | Inconclusivo    | - (estado final)              |
  | Fechado         | - (estado final)              |

- **RN-05:** Todo incidente terminado em fechamento ou inconclusivo registra quem fechou, quando e o motivo.

- **RN-06:** O motorista pode criar incidentes e visualizar apenas os incidentes que ele mesmo reportou. Ele não pode alterar status nem ver incidentes de outros motoristas.

- **RN-07:** Incidente novo: todo incidente é criado com status _Aberto_, sem responsável, e registra o reportante e a data de abertura.

- **RN-08:** Uma alteração só é aplicada se o incidente não tiver sido modificado por outra pessoa desde que o usuário o visualizou. Caso contrário, a alteração é recusada, nada é sobrescrito e o usuário é informado do estado atual do incidente. A regra vale para todos os papéis, inclusive o supervisor.

- **RN-09:** A lista operacional exibe apenas incidentes ativos (_Aberto_ e _Em Investigação_). Incidentes encerrados (_Fechado_ e _Inconclusivo_) ficam disponíveis apenas no histórico.

- **RN-10:** Ao reportar um incidente, a criticidade é sugerida conforme a categoria escolhida, e quem reporta pode alterá-la. A exceção é _Acidente com Vítimas_, que é sempre de criticidade _Alta_ e não pode ser alterada.

  | Categoria                           | Criticidade sugerida |
  | ----------------------------------- | -------------------- |
  | Acidente com Vítimas                | Alta (fixa)          |
  | Acidente com Veículo                | Alta                 |
  | Bloqueio de Pista                   | Baixa                |
  | Condição Climática Atípica na Pista | Média                |
  | Problema Mecânico                   | Média                |

- **RN-11:** Quando um incidente sai de _Em Investigação_ para _Aberto_, o responsável é removido e o incidente volta para a fila de incidentes ativos.

## Histórias de usuário

### US-01: Visualizar incidentes priorizados

**Como** analista da central,
**quero** ver todos os incidentes ativos ordenados por prioridade,
**para** identificar imediatamente o que exige ação urgente.

**Critérios de aceite**

- **Dado** que existem incidentes ativos, **quando** acesso a lista, **então** eles aparecem ordenados conforme a RN-01.
- **Dado** um incidente de criticidade Alta, **quando** ele é exibido, **então** ele se destaca visualmente (cor, ícone e posição) dos demais.
- **Dado** que existem incidentes ativos, **quando** acesso a lista, **então** todos eles são exibidos de uma vez, sem paginação, para que nenhum incidente crítico fique escondido.
- **Dado** um incidente encerrado (_Fechado_ ou _Inconclusivo_), **quando** acesso a lista, **então** ele não aparece na fila (RN-09).
- **Dado** que estou na lista, **quando** olho para o topo da tela, **então** vejo contadores de incidentes por criticidade.

### US-02: Filtrar incidentes por criticidade

**Como** analista da central,
**quero** filtrar incidentes por criticidade,
**para** focar apenas nos incidentes que são mais urgentes.

**Critérios de aceite**

- **Dado** que seleciono uma ou mais criticidades, **quando** aplico o filtro, **então** apenas incidentes ativos com essas criticidades são exibidos.
- **Dado** que apliquei um filtro, **quando** recarrego a página ou compartilho a URL, **então** o filtro é mantido.
- **Dado** que existe um filtro ativo, **quando** clico em "limpar filtros", **então** todos os incidentes ativos voltam a ser exibidos.

### US-03: Filtrar incidentes por categoria

**Como** analista da central,
**quero** filtrar incidentes por categoria,
**para** conseguir tratar incidentes do mesmo tipo em conjunto.

**Critérios de aceite**

- **Dado** que seleciono uma ou mais categorias, **quando** aplico o filtro, **então** apenas incidentes ativos dessas categorias são exibidos.
- **Dado** que combino filtros de criticidade e categoria, **quando** aplico, **então** são exibidos apenas incidentes que atendem a ambos.

### US-04: Visualizar detalhes de um incidente

**Como** analista da central,
**quero** ver todos os detalhes de um incidente,
**para** ter contexto suficiente antes de agir.

**Critérios de aceite**

- **Dado** um incidente na lista, **quando** clico nele, **então** vejo descrição, categoria, criticidade, status, responsável, data de abertura e última atualização.
- **Dado** que o incidente foi fechado, **quando** vejo seus detalhes, **então** vejo quem o fechou, quando e o motivo (RN-05).

### US-05: Assumir um incidente

**Como** analista da central,
**quero** assumir um incidente aberto,
**para** que os outros analistas saibam que eu estou tratando dele.

**Critérios de aceite**

- **Dado** um incidente _Aberto_ e sem responsável, **quando** clico em "Assumir", **então** me torno o responsável e o status muda para _Em Investigação_ (RN-02).
- **Dado** que outro analista assumiu o incidente antes de mim, **quando** clico em "Assumir", **então** recebo um aviso de conflito informando quem o assumiu.
- **Dado** um incidente com responsável, **quando** ele é exibido na lista, **então** o nome do responsável fica visível.

### US-06: Atualizar o status de um incidente

**Como** analista responsável por um incidente,
**quero** alterar seu status,
**para** registrar o andamento da ocorrência.

**Critérios de aceite**

- **Dado** que sou o responsável, **quando** altero o status para uma transição permitida (RN-04), **então** a alteração é salva e a interface reflete a mudança imediatamente.
- **Dado** que não sou o responsável, **quando** tento alterar o status, **então** a ação não está disponível na interface (RN-03).
- **Dado** que o incidente foi modificado por outra pessoa depois que o carreguei, **quando** envio a alteração, **então** recebo um aviso de conflito e vejo o estado atual do incidente (RN-08).
- **Dado** uma falha de rede durante a alteração, **quando** a atualização falha, **então** a interface volta ao estado anterior e oferece a opção "Tentar novamente".
- **Dado** que encerro um incidente, **quando** confirmo a ação, **então** preciso informar um motivo, que fica registrado (RN-05).

### US-07: Alterar qualquer incidente como supervisor

**Como** supervisor de operações,
**quero** alterar o status de qualquer incidente, mesmo sem ser o responsável,
**para** destravar ocorrências paradas ou órfãs.

**Critérios de aceite**

- **Dado** que sou supervisor, **quando** altero o status de um incidente de outro analista, **então** a alteração é aceita (RN-03).
- **Dado** um incidente _Em Investigação_ parado, **quando** o devolvo à fila, **então** ele volta para _Aberto_, sem responsável, e qualquer analista pode assumi-lo (RN-11).
- **Dado** um incidente _Aberto_ e sem responsável, **quando** quero colocá-lo em investigação, **então** preciso assumi-lo e passo a ser o responsável (RN-02).
- **Dado** que o incidente foi alterado por outra pessoa depois que o carreguei, **quando** envio a alteração, **então** recebo um aviso de conflito, como qualquer outro usuário (RN-08).
- **Dado** que encerro um incidente (_Fechado_ ou _Inconclusivo_), **quando** confirmo a ação, **então** preciso informar um motivo, que fica registrado (RN-05).

### US-08: Reportar incidente

**Como** motorista em rota,
**quero** reportar um incidente em poucos toques,
**para** que a central saiba do problema o mais rápido possível.

**Critérios de aceite**

- **Dado** que estou na tela de reporte, **quando** ela é exibida no celular, **então** vejo um formulário curto com categoria, criticidade, local (ex.: "BR-116, km 230") e descrição, com botões grandes e legíveis.
- **Dado** que escolhi uma categoria, **quando** ela é selecionada, **então** a criticidade é preenchida automaticamente com a sugestão para essa categoria, e posso alterá-la (RN-10).
- **Dado** que escolhi _Acidente com Vítimas_, **quando** a categoria é selecionada, **então** a criticidade fica fixa em _Alta_, sem opção de alteração (RN-10).
- **Dado** que preenchi os campos obrigatórios, **quando** envio o reporte, **então** vejo uma confirmação com o número do incidente criado (RN-07).
- **Dado** que deixei um campo obrigatório vazio, **quando** tento enviar, **então** vejo qual campo precisa ser corrigido, sem perder o que já preenchi.
- **Dado** uma falha de rede durante o envio, **quando** a requisição falha, **então** vejo um aviso claro e um botão "Tentar novamente", e os dados preenchidos são mantidos.
- **Dado** que cliquei em enviar mais de uma vez por causa da lentidão, **quando** quando os envios são processados, **então** apenas um incidente é criado.

### US-09: Acompanhar meus reportes

**Como** motorista em rota,
**quero** ver o status dos incidentes que reportei,
**para** saber se a central já está cuidando do problema.

**Critérios de aceite**

- **Dado** que reportei incidentes, **quando** acesso "Meus reportes", **então** vejo apenas os meus incidentes, do mais recente para o mais antigo (RN-06).
- **Dado** que um analista assumiu meu incidente, **quando** vejo a lista, **então** o status aparece como _Em Investigação_.
- **Dado** que ainda não reportei nenhum incidente, **quando** acesso "Meus reportes", **então** vejo um estado vazio com um atalho para reportar.

### US-10: Consultar histórico de incidentes encerrados

**Como** analista da central,
**quero** consultar os incidentes encerrados,
**para** saber quem encerrou cada um, quando e por qual motivo.

**Critérios de aceite**

- **Dado** que existem incidentes encerrados, **quando** acesso o histórico, **então** vejo os incidentes _Fechados_ e _Inconclusivos_, do encerramento mais recente para o mais antigo (RN-09).
- **Dado** que o histórico tem muitos incidentes, **quando** acesso a lista, **então** ela é exibida em páginas, e posso navegar entre elas.
- **Dado** que estou no histórico, **quando** aplico filtros de criticidade, categoria ou status, **então** apenas os incidentes que atendem aos filtros são exibidos.
- **Dado** um incidente no histórico, **quando** clico nele, **então** vejo quem o encerrou, quando e o motivo (RN-05).
- **Dado** que nenhum incidente encerrado atende aos filtros, **quando** a lista é exibida, **então** vejo um estado vazio explicativo, com a opção de limpar os filtros.

### US-11: Entrar no sistema

**Como** usuário do Logos,
**quero** entrar no sistema com minhas credenciais,
**para** que minhas ações sejam identificadas e eu tenha acesso apenas ao que meu papel permite.

**Critérios de aceite**

- **Dado** que acesso a tela de login, **quando** ela é exibida, **então** vejo as credenciais de demonstração de cada papel (analista, supervisor e motorista).
- **Dado** credenciais válidas de analista ou supervisor, **quando** entro no sistema, **então** sou levado à lista de incidentes ativos.
- **Dado** credenciais válidas de motorista, **quando** entro no sistema, **então** sou levado à tela de reporte (RN-06).
- **Dado** credenciais inválidas, **quando** tento entrar, **então** vejo uma mensagem de erro, sem indicar se o erro está no usuário ou na senha.
- **Retirado do escopo do MVP** (RNF-02, [ADR-04](adr/ADR-04-rate-limit.md)). **Dado** que errei a senha várias vezes seguidas, **quando** tento entrar novamente, **então** vejo uma mensagem informando quanto tempo devo esperar.
- **Dado** que estou no sistema, **quando** clico em "Sair", **então** minha sessão é encerrada e volto à tela de login.
- **Dado** que minha sessão expirou, **quando** faço qualquer ação, **então** sou levado à tela de login com um aviso de que a sessão expirou.
- **Dado** que tento acessar uma tela que meu papel não permite, **quando** a página é carregada, **então** sou redirecionado para a minha tela inicial.

## Requisitos não funcionais

| ID     | Categoria      | Requisito                                                                                                                                                                                                                       |
| ------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RNF-01 | Segurança      | Todos os endpoints exigem autenticação, e cada ação é permitida apenas aos papéis autorizados.                                                                                                                                  |
| RNF-02 | Segurança      | **Retirado do escopo do MVP** ([ADR-04](adr/ADR-04-rate-limit.md)). Rate limit: login, 5 tentativas/min por nome de usuário e 20 tentativas/min por IP; criação de incidente, 10/min por usuário; demais rotas, 100/min por usuário. Ao exceder, a API responde HTTP 429 com o cabeçalho `Retry-After`. |
| RNF-03 | Resiliência    | O frontend repete automaticamente requisições de leitura que falharem e mantém os dados em cache durante oscilações de conexão.                                                                                                 |
| RNF-04 | Performance    | A listagem de incidentes ativos responde em menos de 300 ms com até 100 incidentes ativos, em condições normais.                                                                                                                |
| RNF-05 | Usabilidade    | A interface não deve possuir nenhum termo técnico que possa confundir o usuário.                                                                                                                                                |
| RNF-06 | Acessibilidade | A criticidade nunca é comunicada apenas por cor. Sempre acompanha texto ou ícone.                                                                                                                                               |
| RNF-07 | Responsividade | As telas do motorista são projetadas primeiro para celular (mobile-first), com áreas de toque de pelo menos 44 × 44 px.                                                                                                         |
| RNF-08 | Resiliência    | A API aplica tempo limite de 5 s às operações no banco de dados. Se o banco estiver indisponível ou não responder a tempo, responde HTTP 503 com uma mensagem clara, sem expor detalhes internos. A repetição automática das leituras pela própria API foi **retirada do escopo do MVP**: quem repete é o frontend (RNF-03). |
| RNF-09 | Integridade    | Todas as regras de negócio são validadas no servidor, independentemente da interface. Uma ação não permitida é rejeitada mesmo que seja enviada diretamente à API.                                                              |
