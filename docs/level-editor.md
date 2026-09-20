# Atelier — editor visual, versão 0.17

## Começar

Abre **Editor.cmd**. Também podes executar:

```powershell
.venv\Scripts\python.exe -m examples.editor
```

O editor abre uma cópia em memória de um pequeno nível com duas plataformas, dois cristais, checkpoint e perigo. Ainda não existe um ficheiro pessoal guardado. **Ctrl+S** sugere `levels/meu-nivel.json`; podes escolher outro nome. O modelo original e os jogos de exemplo não são alterados ao abrir o editor.

Para começar sem decoração, usa **Novo** e escolhe **Clássico**, **Precisão**, **Salas** ou **Combate**. Os dois primeiros criam chão, ponto inicial e saída; Salas cria duas salas ligadas por portas e uma saída final. Se existirem alterações por guardar, podes guardá-las, descartá-las ou cancelar. Escape fecha a escolha sem criar nada.

**Editor-Precisao.cmd** abre uma cópia de Ascensão com escadas, sinais e movimento avançado. **Editor-Salas.cmd** abre uma cópia do Arquivo Lunar com duas salas, portas, elevador e plataforma horizontal. Os originais ficam intactos. Consulta o [guia dos perfis e salas](editor-profiles.md) para criar e ligar estes objetos.

**Editor-Mecanismos.cmd** abre a Central de Energia no perfil Salas. **T** coloca interruptores; o painel permite configurar ativação e condições para interruptores, portas e saídas. Consulta [eventos e mecanismos](events-and-mechanisms.md).

No teste do perfil Salas, **F6/F9** guardam/carregam progresso temporário em memória. Essa gravação é descartada ao regressar ao editor e não toca nos ficheiros das partidas normais. **Ctrl+S** continua a guardar o documento. Consulta [guardar e retomar uma partida](saving-progress.md).

## Interface

- **Barra superior:** Novo, Abrir, Guardar, Guardar como, Desfazer, Refazer, Validar e Testar.
- **Ferramentas à esquerda:** seleção, sólidos, plataformas, borracha e os objetos permitidos pelo perfil. Nos mundos, **Salas…** abre a gestão das salas.
- **Centro:** mapa em coordenadas de mundo, com grelha.
- **Painel à direita:** propriedades do objeto selecionado, lista de objetos e miniatura de navegação.
- **Rodapé:** erros/avisos, estado da última operação e caminho do ficheiro.

O ponto junto ao nome indica alterações por guardar. Depois de guardar, aparece um visto. Desfazer até à versão guardada também limpa esse indicador.

## Desenhar tiles

Escolhe **1 — Chão sólido**, **2 — Plataforma**, **3 — Borracha**, **U — Rampa /** ou **B — Rampa \**. Prime o botão esquerdo e arrasta pelo mapa. Mesmo um movimento rápido preenche o segmento entre as posições do rato. Um traço completo conta como uma operação para desfazer.

O botão direito apaga tiles quando está selecionada uma ferramenta de tiles. As plataformas finas só colidem pelo topo; os sólidos colidem em todos os lados.

Tiles e objetos são dados separados. Os botões **Tiles** e **Objetos** alternam a sua visibilidade; não alteram as colisões nem removem dados. **Grelha**, ou a tecla **G**, apenas altera a apresentação.

## Colocar e editar objetos

| Tecla | Ferramenta |
|---|---|
| V | Selecionar/mover |
| 4 | Ponto inicial |
| 5 | Cristal |
| 6 | Checkpoint |
| 7 | Perigo |
| 8 | Saída |

Clica numa célula para colocar um objeto. A base fica alinhada com a base dessa célula: para pôr o jogador no chão, clica na célula **imediatamente acima** do chão. A ferramenta de ponto inicial move o spawn existente em vez de criar um segundo.

Os novos objetos recebem IDs únicos. Com **V**, seleciona um objeto e arrasta-o. Por defeito, os deslocamentos seguem a grelha; mantém **Alt** para deslocar por unidades individuais. Podes também selecionar pela lista à direita, incluindo objetos que estejam fora da vista. A roda do rato sobre a lista percorre os objetos.

No painel de propriedades:

- Clica no ID para o editar.
- Clica num valor **X**, **Y**, **W** ou **H** para escrever um número; os botões `−`/`+` alteram uma unidade.
- As setas deslocam o objeto uma unidade; **Shift + seta** desloca oito.
- **Delete** ou o botão Eliminar removem o objeto. A operação pode ser desfeita.

O corpo físico do jogador mede **24×30**, independentemente de W/H do objeto spawn. W/H nos outros objetos definem a área de interação/dano usada no jogo clássico. A arte do exemplo é simples e nem todos os desenhos mudam proporcionalmente com essas dimensões; usa as caixas do editor e F1 no teste para inspecionar colisões.

## Navegar e mudar o tamanho

- **Roda sobre o mapa:** zoom em torno do cursor.
- **Botão central + arrastar:** deslocar a vista.
- **Setas sem seleção:** deslocar a vista.
- **− / + / 1:1:** ajustar ou repor o zoom.
- **Escape na edição:** limpar a seleção.

O botão **Nome** altera o título do nível. **Tamanho** aceita `largura x altura` em tiles, por exemplo `60 x 18`. Aumentar acrescenta células vazias; reduzir corta os tiles fora da nova área, com confirmação e possibilidade de desfazer. Os objetos são mantidos: se ficarem fora da nova área, a validação indica-os para correção.

Nos perfis Clássico e Precisão, novos tamanhos podem variar de 8 a 256 colunas e de 8 a 128 linhas. Ao abrir ficheiros existentes, o editor aceita grelhas menores, até ao mesmo máximo. O tamanho dos tiles é conservado ao abrir, entre 8 e 128 unidades; o editor não o altera pela interface nesta versão. O perfil Salas usa ecrãs fixos de **960×576 unidades** (30×18 tiles de 32); outro tamanho é rejeitado.

## Testar imediatamente

Prime **F5** ou clica em **Testar**. Não precisas de guardar primeiro. O editor valida o documento e inicia o jogo com uma cópia da definição atual:

- A/D ou setas: mover.
- Espaço/Z: saltar.
- Baixo + salto: descer por plataforma fina.
- R: regressar ao checkpoint.
- F1: debug do jogo.
- P/N: pausa e avanço de uma atualização.
- **F5 ou Escape:** regressar ao editor.

Recolher cristais, ativar checkpoints e morrer durante o teste não altera o documento. Cada novo teste começa do início. A posição da vista e o histórico de edição mantêm-se ao regressar.

## Validar

**F8** abre a lista de problemas. Usa a roda para percorrer os resultados; **Ver** centra a vista no problema e seleciona o objeto quando possível.

**Erros geométricos que bloqueiam guardar/testar:** ponto inicial em falta ou repetido, saída em falta, IDs repetidos, objetos fora dos limites, reaparecimento dentro de um sólido ou de um perigo, cristal ou saída totalmente cobertos por sólidos/perigos.

**Avisos que permitem continuar:** ponto de reaparecimento sem apoio imediato, sobreposições parciais com sólidos/perigos e saídas sobrepostas. Um objeto no ar pode ser intencional; o aviso ajuda a conferir o desenho.

No **perfil Clássico**, sem erros geométricos, F8 inicia também uma pesquisa de solução com a física e as definições de movimento do teste. A janela continua a responder; Escape cancela a pesquisa. Nos perfis Precisão e Salas, F8 verifica a estrutura e apresenta explicitamente que a solução jogável requer teste manual.

- **Solução confirmada:** encontrou e repetiu uma rota que recolhe todos os cristais e chega a uma saída, sem mortes. **Ver solução** reproduz essa rota no próprio jogo. F5/Escape regressa ao editor. A rota pode usar R para voltar ao início/checkpoint; o resultado indica quando isso acontece.
- **Fora do alcance:** um cristal obrigatório, ou todas as saídas, estão fora de um limite generoso de salto e deslocação, mesmo ignorando paredes e perigos. O botão **Ver** localiza o objeto. Este diagnóstico não impede guardar ou testar manualmente.
- **Inconclusivo:** a pesquisa não encontrou uma rota dentro do orçamento de 16 000 estados explorados ou cerca de 8 segundos de cálculo. **Não significa que o nível seja impossível.** São indicados os cristais ainda não alcançados durante a pesquisa.

O resultado é invalidado quando se altera o mapa ou as definições de movimento. A pesquisa considera aceleração, salto variável, plataformas finas, checkpoints, perigos e a necessidade de obter todos os cristais numa única partida. Confirma existência de uma rota, não facilidade ou diversão. Não é um decisor universal: pode ficar inconclusiva em mapas complexos e não abrange portas entre salas, elevadores ou inimigos. Desde a fase 20, a Aventura sem combate também tem uma pesquisa própria, descrita abaixo.

No teste clássico, tocar num perigo tem prioridade sobre recolher cristais ou ativar uma saída no mesmo instante, independentemente da ordem dos objetos no ficheiro.

## Guardar e abrir

**Ctrl+S** guarda no ficheiro atual, ou pede um caminho na primeira gravação. **Ctrl+Shift+S** permite guardar como outro ficheiro. Escreve um caminho terminado em `.json`. Caminhos relativos usam a pasta de trabalho, que o lançador define como a pasta deste projeto.

**Ctrl+O** abre a caixa de abertura. Até quatro mapas de `levels/` e os três exemplos suportados aparecem como atalhos; clica para preencher o caminho e confirma. Podes escrever outro caminho, incluindo um caminho absoluto. O perfil é reconhecido ao abrir. Caminhos adicionais continuam acessíveis escrevendo o nome completo.

Abrir um mapa existente passa a editar esse ficheiro. Usa **Guardar como** para criar uma cópia antes de alterar um exemplo. Um destino diferente que já exista exige confirmação antes de substituir.

A gravação valida o mapa, escreve um ficheiro temporário na mesma pasta e só depois substitui o destino. Se falhar, o documento continua marcado como alterado. Não há autosave nem histórico de ficheiros em disco: guarda regularmente. O histórico de desfazer é mantido durante a sessão, até 100 operações; não é guardado no JSON.

Para jogar um mapa guardado fora do editor:

```powershell
.venv\Scripts\python.exe -m examples.classic --map levels\meu-nivel.json
```

## Atalhos principais

| Atalho | Ação |
|---|---|
| Ctrl+N / Ctrl+O | Novo / Abrir |
| Ctrl+S / Ctrl+Shift+S | Guardar / Guardar como |
| Ctrl+Z | Desfazer |
| Ctrl+Y ou Ctrl+Shift+Z | Refazer |
| F8 | Validar |
| F5 | Testar / regressar |
| 1–8 / V | Ferramentas / seleção |
| Delete | Remover objeto selecionado |
| G | Alternar grelha |
| Escape | Cancelar diálogo, limpar seleção ou regressar do teste |

## Âmbito desta entrega

O editor suporta três perfis: Clássico; Precisão (escadas e sinais, com dash e wall jump no teste); e Salas (entradas, portas e plataformas móveis). Inimigos, NPCs e outros objetos não suportados são rejeitados com uma mensagem explícita, sem os remover silenciosamente. Os perfis não são misturados nem convertidos automaticamente.

Também não há seleção múltipla, copiar/colar regiões, pincéis de sprites, camadas artísticas, importação TMX ou edição de animações. Cada perfil usa os controlos e capacidades do respetivo exemplo. A pesquisa automática de soluções continua exclusiva do Clássico.

## API e verificação

`MapDocument`, em `platform2d.tools.editor_model`, pode ser usado sem janela para editar e validar. `MapDocument.load` devolve um `WorldDocument` quando abre um mundo. `LevelEditor` recebe uma função que cria a cena de teste, bindings e, opcionalmente, o dicionário `profiles`. Os adaptadores `examples.editor.profiles` fornecem as três cenas e respetivos comandos, mantendo as dependências dos jogos fora do pacote do editor.

`ReachabilitySearch(data, movement).run()` faz a análise sem interface; `step()` permite distribuí-la por atualizações. O resultado inclui `status`, `issues` e `actions` para repetir uma solução. `LevelEditor` recebe `analysis_movement`; ao integrar outro jogo, é necessário garantir que as regras e o corpo 24×30 correspondem ao perfil clássico antes de usar este verificador.

```python
document = MapDocument.load("levels/meu-nivel.json")
document.paint_line((4, 12), (10, 12), "=")
document.commit()  # agrupa o traço numa operação de histórico
issues = document.validate()
document.save()
```

Para verificar a entrega:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tools\check_editor_workflow.py
.venv\Scripts\python.exe tools\check_reachability.py
.venv\Scripts\python.exe tools\check_advanced_editor.py
cmd /c Editor.cmd --headless --frames 3 --screenshot artifacts\editor.png
```

O fluxo automático usa eventos de rato/teclado para editar, guardar, reabrir e jogar. Confirma a conclusão do nível e que o documento fica intacto depois do teste. `tools/build_editor_template.py` reconstrói **e substitui** apenas o modelo incluído no editor, não os mapas pessoais em `levels/`.


## Áudio (0.9.0)

Os jogos e os testes do editor partilham os comandos F10 (silêncio) e F11/F12 (volume). O serviço é opcional nas cenas e gerido pela aplicação anfitriã. Consulta [áudio e feedback](audio-and-feedback.md).


## Comandos e gamepad (0.10.0)

F3 abre o painel de comandos durante o jogo ou o teste manual do editor. As preferências por perfil são independentes dos mapas e do progresso. O painel suspende a simulação e usa o mesmo serviço de input combinado (teclado/gamepad) em todos os exemplos. Consulta [comandos e gamepad](controls-and-gamepads.md).


## Rampas (0.11.0)

**Editor-Rampas.cmd** abre Colinas no perfil Clássico. As ferramentas U/B estão disponíveis nos três perfis, com pintura, desfazer/refazer e teste integrado. Consulta [rampas e terreno](slopes-and-terrain.md), incluindo os cuidados de validação em mapas inclinados.


## Combate à distância (0.12.0)

**Editor-Combate.cmd** abre Linha de Defesa. No perfil Combate, **5** coloca alvos e **T** coloca torretas. O inspetor configura a resistência e os disparos das torretas; **Arma do jogador…**, à esquerda, configura os tiros do jogador. Todas estas alterações suportam desfazer/refazer e são guardadas no mapa. O perfil usa 960×576 unidades e valida a estrutura, sem pesquisa de solução de combate. Consulta [projéteis e combate](projectiles-and-ranged-combat.md) e o [guia de aprendizagem](learning-projectiles.md).

## Recolhíveis (0.13.0)

**Editor-Inventario.cmd** abre Arsenal de Campo no perfil Combate. **I** coloca um recolhível; **Configurar recolhível…** escolhe Potência, Cadência ou Kit médico e a quantidade. O editor valida o catálogo, os limites e objetos bloqueados por sólidos/perigos. Desfazer/refazer, gravação e teste integrado incluem os novos objetos. Consulta [inventário e melhorias](inventory-and-upgrades.md).


## Salas de missão (0.16.0)

No perfil Combate, C coloca cristais obrigatórios. Missão / ambiente configura o tema e os disparos. A saída exige todos os cristais e alvos; melhorias são opcionais. Consulta [salas e missões variadas](varied-campaign.md).


## Aventura (0.17.0)

Editor-Aventura.cmd abre a oficina do foguetão. O novo perfil inclui peças, combustível, foguetão e mapas maiores, com escolha de movimento e câmara em Missão / ambiente. F5 usa o controlador e o scroll configurados no mapa. Consulta [a documentação da Odisseia](odyssey.md).


## Duelo (0.18)

**Editor-Duelo.cmd** abre um modelo de Aventura com espada e defesa. **Q** coloca um Guardião; a propriedade Vida permite 1–20 pontos. F5 usa as novas ações J/L, configuráveis em F3. Em Missão / ambiente podes escolher o modo Espada e defesa, com disparos desativados e câmara móvel. Consulta [o guia do duelo](sword-and-defence.md).


## Campanhas (0.19)

**Editor-Campanhas.cmd** abre a sequência da Odisseia como uma cópia por guardar. O Atelier também oferece **Novo → Campanha** e reconhece manifestos ao abrir. O espaço de campanhas permite organizar etapas e abrir o editor de cada mapa; **F4** regressa ao espaço anterior. Consulta [o guia completo](campaign-editor.md).


## Pesquisa de percursos de Aventura (0.20)

**F8** passa a procurar soluções para voo, plataformas e bordas sem adversários. Uma rota vencedora é repetida nas regras reais antes de disponibilizar **Ver solução**. A pesquisa é limitada; o resultado pode ser inconclusivo. Consulta [os resultados e limites](adventure-validation.md).
