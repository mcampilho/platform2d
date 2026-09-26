# Platform2D · vigésima entrega

Um núcleo modular em **Python + Pygame**, acompanhado pelo pequeno jogo **Estação Aurora**. Recolhe oito cristais e chega ao portal. Os gráficos são originais, gerados para esta demonstração; não são necessários recursos externos.

A versão **0.2.0** acrescenta **Arquivo Lunar**: duas salas de ecrã fixo, elevador, plataforma de travessia, portas com transição e progresso preservado durante a sessão. Ambos os exemplos usam o mesmo corpo, controlador, física e sistema de animação.

A versão **0.3.0** acrescenta **Sentinelas**: guardas com patrulha, visão limitada por obstáculos, perseguição à última posição vista, dano, golpes curtos, diálogo e um terminal que abre a saída. Os sistemas de estados, perceção, combate e interação são módulos reutilizáveis; as regras da missão pertencem à demonstração.

A versão **0.4.0** acrescenta **Ascensão**: escadas, dash em oito direções, salto na parede e deslizamento controlado. As capacidades são opcionais num novo `PrecisionController`; os exemplos anteriores continuam com `ArcadeController`.

A versão **0.5.1** acrescenta **Atelier**, um editor visual para mapas do jogo clássico: pintura de tiles, colocação e propriedades de objetos, desfazer/refazer, zoom, validação, gravação JSON e teste jogável imediato. F8 procura uma solução completa e permite reproduzi-la; deteta também objetos bloqueados e alvos fora do alcance. O editor abre um modelo próprio; não altera os exemplos existentes ao arrancar.

A versão **0.6.0** amplia o Atelier com os perfis **Precisão** e **Salas**: escadas e sinais; gestão de várias salas; entradas e portas com seleção de destino; elevadores e plataformas móveis com percurso e velocidade editáveis. F5 usa o jogo e os comandos do perfil escolhido. A validação estrutural inclui todas as salas e ligações; nesta versão, a pesquisa automática de soluções era exclusiva do Clássico.

A versão **0.7.0** acrescenta **Central de Energia**: interruptores manuais ou por contacto, portas e saídas condicionadas, dependências entre interruptores e notificações de eventos reutilizáveis. Os mecanismos são configurados no perfil Salas do Atelier. Abre **Jogar-Mecanismos.cmd** para jogar ou **Editor-Mecanismos.cmd** para editar o novo modelo. Consulta [eventos e mecanismos](events-and-mechanisms.md).

A versão **0.8.0** acrescenta **gravação e carregamento de progresso** no Arquivo Lunar e na Central de Energia: **F6 guarda; F9 retoma no checkpoint**, conservando cristais, mecanismos, plataformas e estatísticas. Os ficheiros são versionados e rejeitam mapas/regras incompatíveis. No teste do Atelier, F6/F9 usam apenas memória. Consulta [guardar e retomar uma partida](saving-progress.md).

A versão **0.9.0** acrescenta **áudio reutilizável** nos cinco jogos e no teste do editor: 15 efeitos originais, volume e silêncio. **F10 liga/desliga o som; F11/F12 ajustam o volume.** Sem dispositivo de áudio, o jogo continua normalmente. Consulta [áudio e feedback](audio-and-feedback.md).

A versão **0.10.0** acrescenta **comandos configuráveis e gamepad**: prime **F3** num jogo ou no teste do editor para alterar teclas e botões, ajustar a zona morta do analógico e guardar preferências por perfil. Teclado e gamepad podem ser usados em conjunto. Consulta [comandos e gamepad](controls-and-gamepads.md).

A versão **0.11.0** acrescenta **rampas de 45° nos dois sentidos**, física de subida/descida e ferramentas **U/B** no editor. **Jogar-Rampas.cmd** abre **Colinas**, com sete cristais, checkpoints e um fosso; **Editor-Rampas.cmd** abre uma cópia para editar. As rampas são atravessáveis por baixo. Consulta [rampas e terreno](slopes-and-terrain.md).

A versão **0.12.0** acrescenta **projéteis e combate à distância**: **Jogar-Projeteis.cmd** abre **Linha de Defesa**; mantém **K/X** para disparar. **Editor-Combate.cmd** abre o novo perfil, com alvos, torretas e parâmetros editáveis. Consulta [projéteis e combate](projectiles-and-ranged-combat.md) e o [guia de aprendizagem passo a passo](learning-projectiles.md).

A versão **0.13.0** acrescenta **inventário e melhorias recolhíveis**: **Jogar-Inventario.cmd** abre **Arsenal de Campo**, com potência, cadência e kits médicos. **H usa um kit** (Y no gamepad). **Editor-Inventario.cmd** permite configurar os recolhíveis e testá-los no perfil Combate. Consulta [inventário e melhorias](inventory-and-upgrades.md) e o [guia de aprendizagem desta fase](learning-inventory.md).

A versão **0.14.0** acrescenta **campanhas lineares**: **Jogar-Campanha.cmd** abre **Operação Aurora**, com três níveis de dificuldade crescente. Enter avança após a vitória, conservando melhorias e kits; F2 reinicia toda a campanha. Consulta [campanhas](campaigns.md) e o [guia de aprendizagem](learning-campaigns.md).

A versão **0.15.0** reúne **gravação de campanhas, menus e apresentação**: **Jogar-Campanha.cmd** abre o ecrã inicial com Nova campanha, Continuar e Opções. F6 guarda, F9 carrega com confirmação e Esc/P abre a pausa. Inclui gravação automática nos checkpoints, partículas e transições com efeitos reduzidos opcionais. Consulta [a experiência de campanha](campaign-experience.md) e o [guia de aprendizagem em três etapas](learning-campaign-experience.md).

A versão **0.16.0** acrescenta **Expedição Aurora**: quatro salas diferentes de combate, recolha, travessia perigosa e missão mista. **Jogar-Expedicao.cmd** abre estas quatro salas; **Jogar-Campanha-Classica.cmd** conserva a anterior e as suas gravações. O editor ganha cristais de missão e configuração de ambiente/disparos. Consulta [salas e missões variadas](varied-campaign.md).

A versão **0.17.0** acrescenta **Odisseia Aurora**: começa por voar, montar e abastecer um foguetão; mantém as quatro salas da Expedição e termina com um vale de scroll lateral e um palácio de scroll vertical com bordas agarráveis. Os cenários têm três planos de parallax. **Jogar-Odisseia.cmd** conserva os sete níveis; **Editor-Aventura.cmd** abre o novo perfil. Consulta [voo, foguetão e bordas](odyssey.md) e o [guia de aprendizagem](learning-odyssey.md).

A versão **0.18.0** acrescenta **espada e defesa**, resistência e um Guardião com ataques anunciados. **Jogar-Duelo.cmd** testa o novo encontro; **Jogar-Campanha.cmd** reúne oito etapas e **Editor-Duelo.cmd** abre o modelo editável. O foguetão passa a ter motor, depósito e cockpit, montagem ordenada e abastecimento visível na cor da nave. Consulta [espada e defesa](sword-and-defence.md) e o [guia de aprendizagem](learning-sword.md).

A versão **0.19.0** acrescenta o **editor visual de campanhas**: **Editor-Campanhas.cmd** permite escolher mapas, ordenar etapas, definir o início, validar referências e testar a sequência ou apenas as etapas a partir da seleção. Inclui edição dos mapas, histórico e gravação com caminhos relativos. Consulta [o editor de campanhas](campaign-editor.md) e o [guia de aprendizagem](learning-campaign-editor.md).

A versão **0.20.0** amplia **F8** com pesquisa de percursos de Aventura: voo, montagem e abastecimento do foguetão, plataformas e bordas. Uma solução só é confirmada após repetição nas regras reais; **Ver solução** mostra o percurso. Combate e pesquisas esgotadas ficam explicitamente inconclusivos. Consulta [validar aventuras](adventure-validation.md) e o [guia de aprendizagem](learning-adventure-validation.md).

A versão **0.21.0** melhora a **apresentação das ações**: transporte com braços levantados, poses articuladas de espada, defesa, dano e recuperação, Guardião com armadura e marcas de impacto. Mantém os tempos e as regras do jogo. Consulta [as novidades visuais](action-presentation.md) e o [guia de aprendizagem](learning-action-presentation.md).

A versão **0.22.0 — Novos Horizontes** acrescenta quatro níveis: **Fábrica de Carga**, **Torre Inundada**, **Fuga da Estação** e **Laboratório Esquecido**, com caixas e peso, natação e oxigénio, perseguição e salto duplo adquirido. A campanha tem agora **12 níveis**. **Jogar-Novos-Horizontes.cmd** abre apenas os quatro novos; **Jogar-Campanha-8-Niveis.cmd** conserva a sequência anterior e as suas gravações. Consulta [como jogar e editar](new-horizons.md) e o [guia de aprendizagem](learning-new-horizons.md).

A versão **0.23.0** prepara o **SDK instalável sob licença MIT**, o comando `python -m platform2d new` e o jogo independente **Resgate na Estação**, com três setores e distribuição Windows. Consulta [instalação e criação de jogos](using-platform2d.md), [distribuição](distributing-platform2d.md) e [aprendizagem](learning-independent-game.md). Os ZIPs ficam em `artifacts/releases`; **Jogar-Resgate.cmd** abre a aplicação independente.

A versão **0.24.0** consolida oito idiomas, direção visual, temas recarregáveis, câmara e transições, orientação de objetivos e a campanha de 13 níveis. Acrescenta atlas animados declarados nos temas e aplica-os ao guardião, vegetação e chaves da **Mina das Chaves Perdidas**. A ferramenta `platform2d theme check --preview` valida e apresenta estes sprites antes de os integrar num jogo.

## Criar níveis no Atelier

Abre **Editor.cmd** ou executa:

```powershell
.venv\Scripts\python.exe -m examples.editor
```

Escolhe uma ferramenta à esquerda e desenha no mapa. **V** seleciona objetos; o painel da direita permite editar posição, tamanho e ID. **F5** entra no jogo com uma cópia do mapa atual; **F5/Escape** regressa à edição. **Ctrl+S** guarda; o destino inicial sugerido é `levels/meu-nivel.json`. **F8** mostra os problemas encontrados. Consulta [o guia do editor](level-editor.md).

Abre **Editor-Precisao.cmd** para editar uma cópia de Ascensão ou **Editor-Salas.cmd** para editar uma cópia do Arquivo Lunar. **Novo** permite escolher um dos três perfis. No perfil Salas, usa **Salas…** para gerir o mundo, **Destino / condições… → Ligar porta…** para escolher sala/entrada de destino e **Percurso / velocidade…** para configurar plataformas móveis. **T** coloca um interruptor. Consulta [o guia dos perfis](editor-profiles.md).

Inimigos e NPCs ainda não são suportados pelo editor. Tipos não suportados são rejeitados com uma mensagem, sem conversão ou perda de dados.

## Jogar

**Demonstração de precisão:** abre **Jogar-Ascensao.cmd** (sem espaços) ou executa:

```powershell
.venv\Scripts\python.exe -m examples.precision
```

Sobe a escada com **W / ↑**, recolhe o primeiro sinal e salta sobre o fosso usando **Shift esquerdo / C** com uma direção. No último setor, entra por baixo da parede esquerda, encosta às paredes e volta a premir **Espaço** para ganhar altura. O dash recarrega ao aterrar. Recolhe três sinais e chega ao cume; os checkpoints permitem repetir cada setor.

**Demonstração de combate:** abre **Jogar-Sentinelas.cmd** ou executa:

```powershell
.venv\Scripts\python.exe -m examples.sentinels
```

Fala com Íris usando **E**, derrota os dois guardas com **J** ou **X**, ativa o terminal com **E** e atravessa a saída. Cada pressão de ataque inicia um golpe; espera pela recuperação antes de voltar a atacar. A janela identifica-se como **Parte 3 — Sentinelas**.

Neste computador, o ambiente `.venv` já está preparado: abre **Jogar.cmd** ou executa:

```powershell
.venv\Scripts\python.exe -m examples.classic
```

Para a segunda demonstração, abre **Jogar Salas.cmd** ou executa:

```powershell
.venv\Scripts\python.exe -m examples.rooms
```

No Arquivo Lunar, recupera quatro cristais. O elevador dá acesso ao piso superior da primeira sala; a plataforma horizontal atravessa o fosso da segunda. Usa **E** junto às portas para mudar de sala, incluindo o regresso. O checkpoint da segunda sala também funciona quando morres noutra sala.

Numa instalação nova, com Python 3.10 ou superior:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m examples.classic
```

Em macOS/Linux, usa `python3 -m venv .venv` e `.venv/bin/python` nos comandos seguintes. Executa os comandos na pasta do projeto. O pacote instalável contém o motor; os exemplos são executados a partir deste repositório.

| Comando | Ação |
|---|---|
| A/D ou setas | Mover |
| Espaço ou Z | Saltar; manter premido aumenta a altura |
| Baixo + salto | Atravessar uma plataforma fina para baixo |
| E ou seta para cima | Atravessar porta no Arquivo Lunar |
| E ou seta para cima | Falar, avançar diálogo ou usar terminal em Sentinelas |
| J ou X | Iniciar um golpe em Sentinelas |
| W/S ou cima/baixo | Subir/descer escadas em Ascensão |
| Shift esquerdo ou C + direção | Dash em Ascensão; sem direção, segue a orientação atual |
| Espaço junto a uma parede, no ar | Wall jump em Ascensão |
| R | Regressar ao checkpoint |
| F2 | Reiniciar toda a sessão, incluindo cristais |
| F6 / F9 | Guardar/carregar progresso nos jogos de Salas e Mecanismos; no editor, apenas durante o teste atual |
| F1 | Mostrar grelha, colisões, posição, velocidade e estado |
| P | Pausar/continuar |
| N | Avançar uma atualização física durante a pausa |
| Escape | Sair |

O checkpoint e os cristais permanecem ativos após morrer, durante a sessão. Salas e Mecanismos permitem guardar em disco com F6 e carregar com F9. Nestes dois exemplos não há autosave; F2 reinicia a sessão sem apagar a gravação. A aplicação Campanha tem regras próprias: grava automaticamente nos checkpoints e entre níveis; Nova campanha substitui uma gravação compatível após confirmação.

## O que está implementado

- Física a 60 atualizações por segundo e desenho até 120 FPS, com interpolação.
- Input por ações: pressões curtas ficam guardadas até serem consumidas pela simulação.
- Corpo físico com posições contínuas, separado do controlador e da imagem.
- Colisões retangulares por eixo, com pesquisa de cruzamento ao longo do deslocamento contra geometria estática.
- Aceleração, travagem, controlo no ar, velocidade terminal, coyote time, jump buffering e salto variável.
- Plataformas sólidas e unidirecionais, incluindo descida voluntária.
- Câmara suave com antecipação, limites e reinicialização em teletransportes.
- Spritesheet PNG, animações por estado e inversão horizontal.
- Mapa JSON versionado e validado; objetos identificados por IDs estáveis.
- Jogo de exemplo com perigos, colecionáveis, checkpoint, objetivo e reinício.
- Debug, testes automáticos e execução sem janela para validação.
- Plataformas móveis unidirecionais entre dois pontos, transporte do passageiro e deteção de esmagamento contra tetos estáticos.
- Salas com estado separado da definição: objetos recolhidos, variáveis e posição das plataformas.
- Portas e entradas validadas, transição de escurecimento e checkpoints entre salas.
- Máquina de estados com hooks de entrada, atualização e saída.
- Guardas com patrulha, perceção, perseguição da última posição vista, procura, dano e morte.
- Vida, invulnerabilidade temporária, empurrão e ataques com janelas e um impacto por alvo.
- Seleção contextual por prioridade/distância, NPC com diálogo e terminal interativo.
- Capacidades opcionais: dash com uma carga, wall jump, deslizamento em paredes e escadas.
- Recarga por contacto com chão/plataformas móveis, cancelamento por colisão e saída de escada por salto ou dash.
- Editor visual com tiles e objetos separados, arrasto, propriedades numéricas, zoom e miniatura do mapa.
- Histórico de até 100 operações, proteção de alterações por guardar e gravação JSON por substituição atómica.
- Validação de pontos de início/checkpoint, limites, IDs e saída; teste sem alterar o documento.
- Perfis Clássico, Precisão e Salas, com objetos e comandos próprios.
- Histórico global de mundos, atualização das referências ao renomear salas/entradas e seleção de destinos de portas.
- Percursos de plataformas móveis visíveis e editáveis; validação das ligações e do início do mundo.
- Interruptores de ativação única, manuais ou por contacto; condições AND em interruptores, portas e saídas.
- Eventos de ativação reutilizáveis e análise conservadora de dependências bloqueadas.
- Progresso versionado para mundos de salas, com escrita atómica, validação antes de carregar e teste em memória no editor.

## Organização

```text
platform2d/
  core/          ciclo, contrato de cena e input
  physics/       corpo, caixas, colisões e plataformas móveis
  actors/        movimento, capacidades, personagem, estados, perceção e inimigos
  gameplay/      vida, ataques e seleção de interações
  world/         mapas, câmara, salas e estado da sessão
  audio/         efeitos, volume, silêncio e comandos
  rendering/     spritesheet e animação
  tools/         sobreposição de debug, documento e interface do editor
examples/classic/
  scene.py       regras e apresentação do jogo de exemplo
  settings.json  ações e parâmetros de movimento
  assets/        mapa e spritesheet
examples/rooms/
  scene.py       jogo de ecrãs fixos
  settings.json  configuração independente
  assets/        mundo JSON com duas salas
examples/sentinels/
  scene.py       guardas, diálogo, terminal e regras da missão
  settings.json  movimento e comandos, incluindo ataque/interação
  assets/        mapa do posto de vigia
examples/precision/
  scene.py       percurso de precisão com checkpoints
  settings.json  parâmetros e capacidades opcionais
  assets/        mapa de escadas, fosso e paredes
examples/editor/
  __main__.py    adaptação do editor ao jogo clássico
  assets/        modelo inicial independente
tests/           regressões de física, input e integração
docs/            contratos e guia de extensão
```

Consulta [os contratos de arquitetura](architecture.md) e [o guia para criar uma sala](creating-a-game.md).

Para esta entrega, consulta também [salas, portas e plataformas móveis](rooms-and-platforms.md).

O guia da terceira entrega está em [personagens, combate e interação](characters-and-combat.md).

O guia da quarta entrega está em [movimentos avançados e capacidades opcionais](advanced-movement.md).

## Verificar

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tools\check_route.py
.venv\Scripts\python.exe tools\check_rooms_route.py
.venv\Scripts\python.exe tools\check_sentinels_route.py
.venv\Scripts\python.exe tools\check_precision_route.py
.venv\Scripts\python.exe tools\check_editor_workflow.py
.venv\Scripts\python.exe tools\check_reachability.py
.venv\Scripts\python.exe tools\check_advanced_editor.py
.venv\Scripts\python.exe tools\check_mechanisms_route.py
.venv\Scripts\python.exe tools\check_progress_workflow.py
.venv\Scripts\python.exe tools\check_audio_workflow.py
.venv\Scripts\python.exe tools\check_controls_workflow.py
.venv\Scripts\python.exe tools\check_slopes_route.py
.venv\Scripts\python.exe tools\check_ranged_route.py
.venv\Scripts\python.exe tools\check_inventory_route.py
.venv\Scripts\python.exe tools\check_campaign_route.py
.venv\Scripts\python.exe tools\check_campaign_experience.py
.venv\Scripts\python.exe tools\check_varied_campaign.py
.venv\Scripts\python.exe tools\check_adventure_validation.py
.venv\Scripts\python.exe tools\check_campaign_editor.py
.venv\Scripts\python.exe tools\check_expansion.py
.venv\Scripts\python.exe tools\check_action_presentation.py
.venv\Scripts\python.exe tools\check_duel.py
.venv\Scripts\python.exe tools\check_odyssey.py
.venv\Scripts\python.exe tools\check_adventure_editor.py
.venv\Scripts\python.exe -m examples.classic --headless --frames 120 --screenshot artifacts\demo.png
.venv\Scripts\python.exe -m examples.rooms --headless --frames 120 --screenshot artifacts\rooms.png
.venv\Scripts\python.exe -m examples.sentinels --headless --frames 120 --screenshot artifacts\sentinels.png
.venv\Scripts\python.exe -m examples.precision --headless --frames 120 --screenshot artifacts\precision.png
.venv\Scripts\python.exe -m examples.editor --headless --frames 3 --screenshot artifacts\editor.png
```

`check_route.py` atravessa a demonstração através de ações de input, sem teletransportar a personagem: verifica os oito cristais, o portal e a ausência de mortes, e guarda uma imagem em `artifacts/completed.png`.

`check_rooms_route.py` completa o segundo jogo através de input: usa o elevador, atravessa três portas (incluindo uma visita de regresso), usa a plataforma horizontal e recolhe os quatro cristais sem mortes. Guarda `artifacts/rooms-completed.png`.

`check_sentinels_route.py` conversa com o NPC, derrota os dois guardas, ativa o terminal e chega à saída usando apenas ações do jogador. Verifica a conclusão sem mortes e guarda `artifacts/sentinels-completed.png`.

`check_precision_route.py` sobe a escada, atravessa o fosso com dash, executa saltos alternados nas paredes e recolhe os três sinais, apenas através de input. Verifica a conclusão sem mortes e o uso das três capacidades. Guarda `artifacts/precision-completed.png`.

`check_editor_workflow.py` envia eventos de rato/teclado ao editor para pintar, desfazer/refazer, colocar/mover um objeto, guardar e reabrir JSON. Depois conclui o nível no teste integrado e confirma que o documento não mudou. Os resultados ficam em `artifacts/editor-workflow.json` e nas imagens correspondentes.

Para reconstruir a spritesheet e o mapa originais: `.venv\Scripts\python.exe tools\build_demo_assets.py`. **Este comando substitui os dois recursos da demonstração**, pelo que as alterações pessoais devem ser guardadas noutros ficheiros.

## Limites desta versão

Esta entrega cobre vinte e três marcos incrementais, não todo o motor proposto. Inclui rampas de 45° atravessáveis por baixo; não inclui inclinações sólidas, curvas ou música. O gamepad requer reconhecimento pela interface SDL GameController; o painel de comandos usa teclado/rato. A gravação de progresso abrange o perfil Salas e a aplicação Campanha; não inclui os exemplos isolados Clássico, Precisão, Sentinelas ou Combate. O editor guarda mapas e mundos, não sessões; suporta cinco perfis separados (Clássico, Precisão, Salas, Combate e Aventura), sem combinar todas as regras numa única cena. A pesquisa limitada de soluções com reprodução da rota aplica-se ao Clássico e à Aventura sem combate, e pode produzir um resultado inconclusivo. Os restantes modos exigem teste manual. Os perfis Salas e Combate usam ecrãs fixos de 960×576 unidades; Aventura permite mapas até 3840×2048 com câmara móvel. Aventura inclui agarrar bordas de superfícies estáticas sólidas e voo na oficina; inclui agora natação, oxigénio e salto duplo adquirido, mas ainda não cordas. O dash não concede invulnerabilidade e o wall jump usa superfícies estáticas sólidas. O combate inclui golpes curtos em Sentinelas e projéteis retos no perfil Combate; não inclui combos ou inventário de armas equipáveis; Aventura acrescenta duelo com espada e defesa frontal. Os NPCs têm diálogo linear no exemplo; não há ainda árvores de conversa ou rotinas. O solver pressupõe que os corpos começam fora dos sólidos e não resolve sobreposições iniciais. As plataformas móveis têm topo sólido, mas não laterais ou fundo sólidos; a deteção de esmagamento cobre a subida contra geometria estática, não um sistema geral de máquinas móveis. A pesquisa percorre os colisores do mapa; mapas grandes poderão beneficiar de uma grelha espacial.

O controlador descreve os estados de locomoção `idle`, `run`, `jump` e `fall`. A máquina de estados dos inimigos gere o comportamento independentemente desses estados físicos. Os guardas deslocam-se no chão, evitando bordas; não planeiam saltos nem caminhos entre plataformas.

Os pontos 4 e 5 da sequência foram concretizados pelo Resgate e pelo SDK da fase 0.23. A publicação em serviços externos e a verificação noutras máquinas ficam para uma entrega futura.

Referência utilizada para o tratamento de teclas e eventos: [documentação oficial do Pygame](https://www.pygame.org/docs/ref/key.html).
