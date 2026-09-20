# Contratos do núcleo

## Coordenadas e tempo

A origem é o canto superior esquerdo; X cresce para a direita e Y para baixo. Uma unidade de mundo corresponde a um píxel na escala atual de apresentação. As posições são floats; velocidades são unidades/segundo; acelerações são unidades/segundo². Todos os temporizadores recebem segundos. Só a apresentação arredonda as coordenadas.

O `Game` recolhe eventos, acumula tempo e executa passos de 1/60 s. O delta de uma iteração é limitado a 0,25 s para evitar recuperação ilimitada após uma pausa do sistema. Portanto, uma interrupção longa não é simulada integralmente. Não se promete determinismo entre plataformas nem existe sistema de replay nesta versão.

`Input` mantém teclas ativas e flancos de ações. Os flancos permanecem disponíveis quando não ocorre nenhum passo físico e são consumidos no primeiro passo seguinte. Perda de foco liberta as teclas. Escape é um comando da aplicação; as ações do jogo são configuráveis.

## Ordem de uma atualização

1. A cena trata debug, pausa e reinício.
2. O controlador atualiza tolerâncias e intenções de velocidade.
3. A física guarda a posição anterior, resolve X e depois Y e atualiza contactos.
4. O controlador pode executar um salto guardado ao aterrar.
5. A cena trata objetos, perigos, checkpoint e objetivo.
6. A câmara segue o resultado físico.
7. A apresentação atualiza a animação.

O desenho interpola corpo e câmara pelo mesmo alfa. `Body.teleport` e a opção `snap` da câmara sincronizam estados anteriores e atuais, evitando deslocamentos visuais através do nível após um reinício.

## Responsabilidades

`Body`, `Box`, `Collider`, `ArcadeController` e `Camera` não dependem de imagens nem de janelas. `Character` combina corpo e controlador. O estado simples de locomoção deriva do resultado físico; a imagem não determina o movimento.

`Actions` é a fronteira entre um controlador humano e uma futura IA. Um agente pode construir ações e chamar `Character.update` sem gerar eventos de teclado.

`SpriteView` recebe um estado e desenha frames. `ClassicScene` decide as regras dos cristais, perigos e vitória. Essas regras não fazem parte da física.

`Scene` é um protocolo: qualquer objeto que implemente `update(dt, actions)` e `draw(surface, alpha)` pode ser usado por `Game`. Cada exemplo fornece a sua própria cena. `RoomsScene` usa `RoomWorld` para mudar de sala e `FadeTransition` para sincronizar a troca com a apresentação.

## Colisões

Cada eixo testa o cruzamento da face do corpo contra as faces dos sólidos e escolhe a distância mais próxima. Isto evita atravessar paredes finas ao longo de um eixo, mas não é um solver contínuo de trajetórias diagonais arbitrárias. A resolução segue deliberadamente X e depois Y.

Plataformas unidirecionais só bloqueiam deslocamento descendente quando a base anterior do corpo estava acima da sua superfície. A descida voluntária ignora-as temporariamente, mantendo os sólidos ativos.

Os contactos indicam colisões ocorridas no passo. Um corpo em queda recebe gravidade em cada atualização, mantendo o contacto com o chão; os contactos laterais só se mantêm enquanto há movimento contra a parede. Sensores persistentes para escalada ficam fora deste marco.

## Dados e sessão

O mapa descreve a definição inicial. A cena guarda separadamente IDs recolhidos, checkpoint ativo, posição de reaparecimento e contagem de mortes. Reiniciar a sessão descarta esse estado. A lista de objetos do mapa não é alterada para remover cristais.

Não se carregam scripts executáveis de JSON. O formato aceita um conjunto explícito de tipos. Novas regras de jogo podem estender o carregador ou criar o seu próprio formato sem modificar o solver.

## Salas e plataformas — versão 0.2

`RoomWorld` mantém definições, estado por sala e checkpoint de sessão. `RoomState.removed` guarda IDs de objetos removidos; `flags` guarda variáveis do jogo. As salas inativas não avançam, preservando a fase das suas plataformas. `enter` muda a sala e devolve a posição da entrada; a cena teletransporta a personagem. `respawn` restaura a sala do checkpoint e devolve a posição guardada. `reset` limpa todas as salas.

No exemplo de salas, a ordem passa a ser: comandos globais → pausa/transição → plataformas da sala ativa → controlador/física da personagem → objetos/interação → animação. Cada plataforma é atualizada **uma só vez por passo**, mesmo quando existem várias personagens.

`Character.update` aceita o argumento opcional `platforms`. O solver transporta quem estava apoiado no topo anterior, respeitando obstáculos estáticos, e depois resolve o movimento da personagem. A aterragem compara também o movimento relativo entre a base anterior do corpo e o topo anterior da plataforma, para detetar uma plataforma que sobe por baixo do corpo.

Saltar desliga o transporte; descer voluntariamente ignora os topos móveis. O corpo não herda a velocidade da plataforma no salto nesta versão. A subida bloqueada por um teto ativa `Body.crushed`; a cena decide se isso significa morte. A personagem continua sem conhecer recursos gráficos ou regras específicas do exemplo.

Durante as transições, a simulação do mundo fica suspensa e a callback de entrada é executada exatamente uma vez, no ponto de opacidade máxima. A tecla de interação exige uma nova pressão; manter E premido não atravessa automaticamente uma segunda porta.

## Personagens e combate — versão 0.3

`StateMachine` contém estados nomeados com `enter(owner)`, `update(owner, dt)` e `exit(owner)`. Mudar para o mesmo estado não repete hooks; nomes desconhecidos são rejeitados. Uma transição reinicia `elapsed`. Não se permite iniciar outra transição dentro dos hooks de entrada/saída. A máquina não conhece imagens, física ou input.

`PatrolEnemy` combina `Character`, `Health`, perceção e uma máquina com `patrol`, `chase`, `search`, `hurt` e `dead`. A intenção de movimento é convertida em `Actions`, reutilizando o controlador do jogador. A perseguição conserva apenas a última posição observada; durante a perda de visão, não lê a nova posição do alvo para decidir o destino. O alcance é 200 e a abertura visual 110 graus; sólidos bloqueiam a linha de visão entre centros, plataformas unidirecionais não.

`Health` limita dano através de uma janela de invulnerabilidade; o estado morto é terminal até `restore`. `Attack` separa preparação, janela ativa e recuperação. Guarda IDs atingidos por golpe, fixa a direção no início e testa obstáculos antes do impacto. A hurtbox usada no exemplo é a caixa do corpo; a API aceita outra `Box` sem alterar o solver físico.

`Character.knockback` ativa temporariamente um movimento com velocidade imposta e gravidade, durante o qual o controlador não substitui o empurrão. O corpo continua a colidir normalmente. Este estado de movimento não introduz vida nem regras de combate em `Character`.

Em Sentinelas, a ordem é: comandos globais → pausa/diálogo → temporizadores de vida → personagem → janela de ataque → inimigos e impactos → dano de contacto → interação → objetivo → animação. Um golpe que entra na mesma atualização que um contacto tem prioridade. Inimigos em `hurt` não provocam dano de contacto. O diálogo congela a simulação por uma escolha explícita desta cena.

`choose_interaction` apenas seleciona uma ação: maior prioridade, menor distância e ID como desempate estável. A cena executa a callback quando recebe uma nova pressão de interação. As condições de missão e os textos ficam no jogo, não no seletor.

## Capacidades opcionais — versão 0.4

`PrecisionController` estende `ArcadeController` e recebe uma configuração `Abilities`. Dash, wall jump e escadas podem ser desativados independentemente. Com os três desativados, os testes verificam que o movimento coincide com o controlador clássico para a mesma sequência de input.

Antes da física, `Character` passa colisores e escadas ao hook `controller.prepare`. O controlador clássico não usa esse contexto. Escadas são caixas lógicas fornecidas pelo jogo através do argumento nomeado `ladders`; a física continua a resolver os sólidos existentes. Nenhuma capacidade teletransporta o corpo para ultrapassar obstáculos.

A ordem de prioridade é: empurrão/atordoamento → dash → escada → wall jump/impulso temporariamente bloqueado → movimento normal/deslizamento. Dash e escada suspenderem gravidade não altera o solver. `motion_state` fornece os estados visuais `dash`, `climb` e `wall_slide`; não modifica as máquinas de comportamento dos inimigos.

O dash normaliza a direção, conserva uma única carga no ar, cancela ao colidir no seu eixo de movimento e recarrega por contacto com o chão. A recarga considera o contacto antes de um salto guardado ser aplicado, pelo que aterrar e saltar no mesmo passo continua a repor a carga. Um contacto lateral ou uma escada não recarregam. O último passo do dash usa apenas a fração de duração restante, evitando ultrapassar a distância configurada.

`controller.interrupt` cancela movimento especial ao sofrer empurrão. No controlador de precisão preserva a disponibilidade da carga: sofrer dano no ar não concede um dash gratuito. `reset`, usado no reaparecimento, restaura todos os temporizadores e capacidades.

## Autoria visual — versão 0.5

`MapDocument` é o modelo do editor e não depende de uma janela. Conserva a definição JSON, a última versão guardada e duas pilhas de histórico. `begin`/`commit` agrupam todos os pontos de um traço de rato numa operação; o histórico conserva até 100 operações. `undo` e `redo` trocam snapshots independentes. O indicador de alterações compara o documento com o snapshot guardado, incluindo depois de desfazer.

A validação distingue formato não suportado (rejeitado ao abrir) de problemas editáveis, como spawn em falta ou objetos fora dos limites. Problemas geométricos são devolvidos como `Issue`, com gravidade, mensagem e posição quando possível. Erros impedem guardar/testar; avisos permitem continuar. O modelo verifica espaço para o corpo padrão 24×30 e sobreposição com perigos nos pontos de reaparecimento. A análise adicional `ReachabilitySearch` usa o controlador real a 60 Hz, pesquisa limitada e repetição com todos os colisores antes de emitir um certificado positivo. Um grafo otimista de superfícies permite rejeitar alvos fora do alcance; esgotar a pesquisa produz apenas um resultado inconclusivo. O editor distribui o trabalho por atualizações, invalida resultados após alterações e reproduz os comandos através da cena de teste. Erros de alcance não bloqueiam guardar/testar; erros geométricos continuam a bloquear.

`save` valida, escreve um ficheiro temporário na mesma pasta e usa `os.replace` para substituir o destino. Só depois atualiza o snapshot guardado e o caminho. Falhas deixam o documento marcado como alterado. Uma tentativa de guardar dados inválidos não toca no ficheiro existente. Não existe autosave ou salvaguarda de várias versões nesta entrega.

`LevelEditor` contém a interface Pygame, navegação e modais. Recebe uma `preview_factory(level)` e bindings; não importa jogos de exemplo. F5 cria uma cena a partir de um mapa copiado, usa input novo e um acumulador fixo próprio. Regressar descarta a sessão de teste e preserva o documento, o histórico e a posição de edição.

Não se alterou o ciclo `Game` dos exemplos existentes. O editor tem um ciclo próprio porque gere eventos de texto, arrasto, confirmações e alternância entre edição/teste. A proteção contra perda de trabalho aplica-se a Novo, Abrir e fechar a janela. Guardar como pede confirmação se o destino já existir e for diferente do ficheiro aberto.

## Perfis e autoria de mundos — versão 0.6

`MapDocument` reconhece Clássico e Precisão. O marcador `editor_profile` preserva o perfil de precisão quando deixa de haver objetos que o permitam inferir. Os objetos aceites são definidos por perfil; não há conversão silenciosa. `MapDocument.load` encaminha ficheiros com `rooms` para `WorldDocument`.

`WorldDocument` reutiliza as operações sobre tiles e objetos, expondo `data` como a sala ativa. `snapshot` e `restore` operam sobre o mundo inteiro; por isso gravação, indicador de alterações e histórico são globais. A sala visível é estado da interface e não altera o ficheiro. Renomear salas e entradas atualiza portas e início do mundo dentro da mesma transação. Eliminar não apaga referências; a validação identifica-as como erros. `playable()` devolve um `RoomWorld` independente, sem partilhar estado de jogo com o documento.

O dicionário opcional `profiles` de `LevelEditor` fornece, por perfil, `factory`, `bindings` e `size`. `examples.editor.profiles` é o adaptador que conhece `ClassicScene`, `PrecisionScene` e `RoomsScene`. A interface usa o tamanho de desenho de cada cena e preserva as proporções. O perfil de salas limita as dimensões a 960×576, correspondendo à cena de ecrã fixo; não é uma limitação geral de `RoomWorld`.

`Issue.room_id` permite localizar problemas em salas diferentes. A validação de mundos verifica geometria local, entradas, extremos dos percursos, destinos e um grafo dirigido de portas a partir da sala inicial. Cristais em salas sem ligação e ausência de qualquer saída ligada são erros. O grafo não prova alcançabilidade física, nem uma rota que reúna todos os cristais; a interface diz isso explicitamente. A pesquisa `ReachabilitySearch` nunca é aplicada aos perfis Precisão ou Salas, e qualquer certificado clássico anterior é invalidado ao mudar de perfil.

## Eventos e mecanismos — versão 0.7

`core.events.EventBus` publica notificações síncronas a ouvintes por tipo, sem depender de Pygame. `gameplay.mechanisms.Mechanisms` conserva um conjunto de pares `(room_id, switch_id)` ativos. As condições `requires` são conjunções dessas referências. A primeira ativação válida altera o estado e publica `switch_activated`; repetições não voltam a emitir o evento. As condições são monotónicas nesta versão, sem alternância ou desativação.

`RoomWorld` possui o estado de mecanismos, valida o formato e as referências ao carregar, e limpa as ativações no reinício completo. Mudar de sala, reaparecer e morrer preservam o conjunto. `RoomsScene` decide contacto/proximidade, escolhe uma única interação manual e apresenta avisos; portas e saídas consultam as condições antes de permitir a passagem/vitória. O dano é processado antes de ativar mecanismos ou recolher objetivos. Os mapas antigos sem condições conservam a disponibilidade anterior.

O editor conserva referências inválidas para correção e atualiza as referências ao renomear salas/interruptores na mesma transação. `optimistic_access` calcula um ponto fixo: salas alcançadas permitem ativar interruptores cujas condições estão satisfeitas; as ativações permitem abrir mais portas. Considera acesso livre dentro de cada sala e combina possibilidades de caminhos diferentes, pelo que só rejeita bloqueios sob uma aproximação generosa. Condições não satisfeitas geram avisos; bloquear cristais obrigatórios ou todas as saídas gera erros. Nunca emite um certificado de solução física.

O JSON é declarativo, sem execução de expressões, imports ou código. Não se introduz uma linguagem geral de scripting. As regras estão disponíveis no perfil Salas e num novo exemplo que reutiliza a cena e os controlos existentes.

## Progresso persistente — versão 0.8

`gameplay.progress` separa captura, validação, aplicação e armazenamento. O registo de checkpoint contém formato/versão, assinaturas do mundo e movimento, cristais por sala, indicadores de checkpoint, fases de plataformas, interruptores ativos e estatísticas. `RoomWorld.definition` é uma cópia independente da definição de origem, separada dos objetos em execução; a assinatura usa JSON canónico e SHA-256.

`validate_progress` verifica o registo inteiro antes de alterar qualquer estado. Rejeita campos desconhecidos, tipos errados (incluindo booleanos onde se esperam números), versões incompatíveis, posições que não correspondem ao início/checkpoints definidos, sobreposições perigosas nesse ponto, IDs desconhecidos/repetidos, fases inválidas, interruptores sem uma ordem de ativação válida e vitória sem objetivos completos. A validação de consistência não pretende impedir adulteração nem provar uma rota jogável.

`restore_progress` conserva os objetos do mundo e as subscrições de eventos. Aplica coleções, indicadores, mecanismos e fases, define a sala atual como a do checkpoint e devolve estatísticas. A cena reinicia o corpo/controlador, sincroniza interpolação e retira a pausa. A posição exata, velocidade, input, transições e estado de interface não são persistidos. Nenhum evento de ativação é reemitido.

`ProgressSlot(path)` limita a leitura a 2 MiB e usa JSON sem chaves repetidas ou constantes não finitas. A escrita usa um temporário na pasta de destino, flush/fsync e substituição atómica. Antes de substituir um ficheiro existente, verifica que se trata de progresso válido e compatível. Falhas preservam o ficheiro anterior. Não há migração automática nem sobrescrita de ficheiros incompatíveis/danificados.

`RoomsScene` recebe o slot por injeção. Os lançadores de Salas/Mecanismos fornecem um caminho em `saves/` ou `--save-file`; `ProgressSlot()` sem caminho usa memória, permitindo que F6/F9 no Atelier não acedam às partidas normais. F2 reinicia a sessão sem apagar o slot. Durante transições, guardar/carregar é recusado. Os perfis Clássico, Precisão e Sentinelas ainda não usam este formato.


## Áudio (0.9.0)

Os jogos e os testes do editor partilham os comandos F10 (silêncio) e F11/F12 (volume). O serviço é opcional nas cenas e gerido pela aplicação anfitriã. Consulta [áudio e feedback](audio-and-feedback.md).


## Comandos e gamepad (0.10.0)

F3 abre o painel de comandos durante o jogo ou o teste manual do editor. As preferências por perfil são independentes dos mapas e do progresso. O painel suspende a simulação e usa o mesmo serviço de input combinado (teclado/gamepad) em todos os exemplos. Consulta [comandos e gamepad](controls-and-gamepads.md).


## Superfícies inclinadas (0.11.0)

A grelha aceita rampas / e barra invertida, de 45° e atravessáveis por baixo. Os colisores descrevem a inclinação e o motor resolve as transições com o chão plano. Mapas sem rampas mantêm o algoritmo anterior. Consulta [rampas e terreno](slopes-and-terrain.md) para formato, integração, limites e validação.


## Projéteis (0.12.0)

`Weapon` controla a cadência, `ProjectileSystem` move tiros e emite impactos, e a cena aplica dano e efeitos. O perfil Combate usa `properties.weapon` e os objetos `target`/`turret`. O núcleo de projéteis não depende do Pygame. Consulta [projéteis e combate](projectiles-and-ranged-combat.md) e o [guia de aprendizagem desta fase](learning-projectiles.md).

## Inventário (0.13.0)

`Inventory` é independente do Pygame e guarda quantidades limitadas por `ItemDefinition`, com adição e consumo indivisíveis. O objeto de mapa `pickup` fornece tipo e quantidade; a cena guarda separadamente os IDs recolhidos. `upgraded_weapon` deriva uma especificação imutável a partir da arma original e das contagens. `Health.heal` recupera vida sem ressuscitar nem reiniciar a invulnerabilidade. O inventário do perfil Combate dura apenas a sessão. Consulta [inventário e melhorias](inventory-and-upgrades.md) e [o percurso de aprendizagem](learning-inventory.md).


## Campanhas (0.14.0)

`CampaignProgress` gere uma sequência de IDs, conclusão e avanço. `CampaignScene`, no exemplo, coordena cenas de Combate e decide transportar inventário, restaurar vida e acumular estatísticas. Os mapas são validados antes de jogar e continuam independentes do manifesto de campanha. Consulta [campanhas](campaigns.md) e o [guia de aprendizagem](learning-campaigns.md).


## Experiência de campanha (0.15.0)

`CampaignApp` compõe menus, gravação e feedback em torno de `CampaignScene`. O contrato de progresso pertence ao exemplo; `JsonSlot` fornece armazenamento JSON validado e escrita atómica reutilizável. `Feedback` tem apenas estado visual limitado. O anfitrião `Game` aceita eventos opcionais da aplicação, pedido de saída e ocultação das dicas nos menus. Consulta [a experiência de campanha](campaign-experience.md).


## Aventura (0.17.0)

`JetpackController` e `LedgeController` são capacidades opcionais sobre o corpo e as colisões existentes. `RocketMission` gere carga, montagem e combustível sem desenho. `AdventureScene` reutiliza a cena de combate, separando mundo, painel e sobreposição. A fábrica da campanha é partilhada pelo início, mudança de nível e carregamento. Câmara e três camadas de parallax afetam apenas a apresentação. Consulta [o guia de aprendizagem](learning-odyssey.md).


## Espada e defesa (0.18.0)

`Sword` compõe janelas de `Attack`, resistência e defesa direcional. `DuelScene` adapta essas regras à campanha; `Guardian` escolhe ações sobre o mesmo corpo e colisões. O ponto `update_encounters()` resolve o encontro antes da morte e dos objetivos. O progresso conserva IDs de guardiões derrotados. Consulta [a implementação comentada](learning-sword.md).


## Editor de campanhas (0.19.0)

`CampaignDocument` mantém a sequência e referências absolutas durante a edição; exporta caminhos relativos através de escrita atómica. `CampaignEditor` reutiliza os diálogos do Atelier e recebe uma fábrica de `CampaignScene` do anfitrião. As etapas mantêm `MapDocument` e histórico próprios. Testes constroem uma sessão isolada, sem gravações de progresso. Consulta [o guia de aprendizagem](learning-campaign-editor.md).


## Validação de Aventura (0.20.0)

`AdventureSearch` estende a pesquisa de estados com controladores de voo/bordas e o estado de `RocketMission`. Modelos otimistas detetam alguns bloqueios; o limite da procura nunca é interpretado como impossibilidade. A fábrica de cenas do anfitrião certifica rotas candidatas por repetição real antes de expor os comandos ao editor. Consulta [o guia de aprendizagem](learning-adventure-validation.md).


## Apresentação de ações (0.21)

`rendering/action_pose.py` converte estado de combate em poses e desenha figuras articuladas sem avançar a simulação. `RangedScene.draw_player` é o ponto de extensão para transporte em AdventureScene e espada em DuelScene. Marcas de impacto pertencem à cena, envelhecem na atualização e são descartadas no respawn. Não fazem parte do progresso guardado. Consulta [o guia de aprendizagem](learning-action-presentation.md).


## Novos Horizontes (0.22)

`gameplay/cargo.py` gere caixas físicas e peso; `actors/exploration.py` acrescenta controladores de água e salto duplo. `ExpansionScene` compõe estes módulos com os pontos de extensão de Aventura, as regras de oxigénio, perseguição e portas. `prepare_world` fornece geometria dinâmica antes da física; o mapa original é reposto depois da atualização. O progresso acrescenta posições de caixas apenas ao modo Carga e inclui capacidades nos IDs recolhidos. O editor reconhece os novos objetos e declara F8 inconclusivo. Consulta [aprender com os quatro estilos](learning-new-horizons.md).


## SDK e aplicação independente (0.23)

`platform2d.__main__` gera um projeto de jogo a partir de modelos incluídos na wheel. `paths.user_data_dir` separa dados do utilizador de recursos instalados. `games/resgate` é um pacote próprio que declara `platform2d==0.23.0` como dependência e não importa exemplos. O seu construtor Windows executa PyInstaller sobre os pacotes instalados, com recursos explícitos, e permite verificar os percursos também dentro do executável.
