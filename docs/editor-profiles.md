# Sexta entrega — Atelier: precisão e salas

## Começar

| Lançador | Modelo aberto em memória | Gravação sugerida |
|---|---|---|
| Editor.cmd | Clássico, duas plataformas e cristais | levels/meu-nivel.json |
| Editor-Precisao.cmd | Ascensão, escada, dash e paredes | levels/minha-ascensao.json |
| Editor-Salas.cmd | Arquivo Lunar, duas salas e plataformas móveis | levels/meu-mundo.json |

Os modelos são cópias sem ficheiro associado. Alterar e guardar não substitui os exemplos originais. Usa **Novo** para criar um projeto vazio num dos três perfis. **Abrir** reconhece mapas clássicos, mapas de precisão e mundos de salas; neste caso o ficheiro aberto passa a ser o destino de gravação, por isso usa **Guardar como** se quiseres uma cópia.

## Precisão

Além de sólidos, plataformas finas, spawn, checkpoint e saída, tens:

- **5 — Sinal:** colecionável obrigatório (`beacon`). A saída exige todos os sinais.
- **L — Escada:** coloca uma escada com base na célula escolhida. Ajusta X/Y/W/H no painel; a dimensão inicial é 32×96. As travessas no mapa mostram a área de subida.

**F5** usa o controlador de Ascensão: W/S ou cima/baixo nas escadas, Shift esquerdo/C para dash, Espaço para salto e saltos na parede. Os parâmetros vêm de `examples/precision/settings.json`. Não há editor de capacidades nesta entrega; todos os mapas deste perfil usam essas definições. O perfil não oferece perigos ou cristais clássicos porque a cena de precisão não implementa essas regras.

F8 verifica geometria, limites, espaço para reaparecer e sinais/saída bloqueados. **Não aplica o alcance do salto clássico a uma personagem com dash e wall jump.** A confirmação automática da solução não está disponível neste perfil: usa F5.

## Salas

Cada mundo é guardado num único JSON com todas as salas e ligações. **Salas…**, à esquerda, permite:

1. Escolher uma sala para editar (usa a roda se houver mais de seis).
2. **Adicionar** uma sala com chão e spawn; escreve um ID único.
3. **Mudar ID** da sala atual; as portas de destino e o início do mundo são atualizados na mesma operação.
4. **Eliminar** a sala atual, com confirmação. As ligações quebradas ficam visíveis em F8; não são removidas silenciosamente. A última sala não pode ser eliminada.

O botão **Nome** altera o título da sala atual. O ID é a referência usada pelas portas; pode ser diferente do título. O histórico de desfazer/refazer abrange **o mundo inteiro**, incluindo mudanças feitas noutras salas. Mudar a sala visível não é uma alteração ao documento.

As salas têm dimensões fixas de **960×576 unidades**, correspondentes a 30×18 tiles de 32. Este limite corresponde ao jogo de ecrãs fixos usado no teste. Usa o zoom ou desloca a vista para ver toda a sala.

## Entradas e portas

Uma **entrada** define onde aparece o corpo de 24×30 ao atravessar uma porta. Uma **porta** é a área onde o jogador prime E para sair. São objetos distintos, e não precisam de estar sobrepostos.

1. Na sala de destino, usa **I — Entrada** e coloca-a com espaço livre e apoio. O spawn da sala também pode receber uma porta.
2. Na sala de origem, coloca **O — Porta**.
3. Seleciona a porta e clica em **Destino / condições…**, depois em **Ligar porta…**.
4. Escolhe a sala e depois a entrada. Só aparecem destinos existentes.
5. Para regressar, cria outra porta na sala de destino e liga-a a uma entrada da primeira sala. As ligações são direcionais: criar uma não cria automaticamente a inversa.

O destino atual aparece por baixo do ID da porta. Mudar o ID de uma entrada atualiza todas as portas que a referenciam. Eliminar uma entrada deixa um erro explícito nas portas afetadas, a corrigir antes de guardar/testar.

Para escolher o início da partida, seleciona um **spawn** ou **entrada** e clica em **Definir início do mundo**. O gestor de salas assinala a sala inicial. Cada sala conserva um spawn próprio, mesmo quando não é a sala inicial.

## Elevadores e plataformas móveis

Usa **M — Plat. móvel**. A plataforma aparece com uma linha até ao destino, e um retângulo indica a posição final.

- X/Y definem o ponto inicial; W/H definem as dimensões.
- **Percurso / velocidade…** permite editar Destino X, Destino Y e velocidade em unidades por segundo.
- Mesmo X nos dois pontos: elevador vertical. Mesmo Y: travessia horizontal. Também são aceites trajetos diagonais.
- A plataforma vai e volta automaticamente. Transporta o jogador pelo topo; não tem paredes laterais nem fundo sólido.

Arrastar a plataforma altera **o ponto inicial**; o destino mantém as coordenadas definidas. F8 exige um percurso não vazio, velocidade positiva e ambos os extremos dentro da sala. A área do percurso cruzar sólidos produz um aviso conservador: em trajetos diagonais pode incluir zonas que a plataforma não atravessa. Testa sempre o transporte e o risco de esmagamento com F5.

## Validar e testar um mundo

F8 verifica todas as salas, não apenas a visível. **Ver** muda para a sala do problema e centra o objeto quando aplicável. São erros:

- Spawn em falta/repetido, IDs duplicados dentro da sala, objetos fora dos limites, entradas/checkpoints sem espaço seguro.
- Portas sem destino, salas/entradas de destino inexistentes, início do mundo inválido.
- Plataforma com destino fora da sala ou percurso vazio.
- Ausência de uma saída final no mundo.
- Sala com cristais obrigatórios sem qualquer ligação desde o início, ou nenhuma saída final ligada ao início.

Uma sala sem ligação e sem cristais produz um aviso. Sobreposições de portas/saídas, posições sem apoio e possíveis conflitos no percurso das plataformas também produzem avisos. O grafo das ligações é dirigido: segue apenas as portas no sentido em que foram configuradas.

**Uma ligação existente não prova que o jogador chega fisicamente à porta, nem que pode recolher todos os cristais numa única rota.** F8 indica esta limitação. A confirmação de solução e reprodução automática de 0.5.1 continuam a funcionar no perfil Clássico; ainda não analisam dash, escadas, portas ou plataformas móveis.

F5 inicia sempre no início configurado do mundo, mesmo que estejas a editar outra sala. Usa E junto às portas. Os cristais recolhidos e a fase das plataformas ficam preservados ao mudar de sala durante o teste; a saída final exige todos os cristais do mundo. F5/Escape regressa ao editor. O teste não altera o documento nem o histórico.

## Ficheiros e execução

O formato dos mundos continua a ser o usado pelo Arquivo Lunar: `version: 1`, `rooms`, `start_room` e `start_entry`. Os mapas de precisão conservam `editor_profile: "precision"`, mesmo que removas todas as escadas e sinais. Os IDs dos objetos são únicos dentro da respetiva sala.

```powershell
.venv\Scripts\python.exe -m examples.editor --profile rooms
.venv\Scripts\python.exe -m examples.editor --profile precision
.venv\Scripts\python.exe -m examples.editor --map levels\meu-mundo.json
.venv\Scripts\python.exe -m examples.rooms --world levels\meu-mundo.json
.venv\Scripts\python.exe -m examples.precision --map levels\minha-ascensao.json
```

O formato é reconhecido ao abrir; não há conversão entre perfis nem combinação de precisão com salas nesta entrega. Os mapas de Sentinelas, inimigos, NPCs e outros tipos não suportados continuam a ser rejeitados sem perda silenciosa de dados. Também não são acrescentados scripting, áudio ou gravação de progresso de jogo.

Na versão 0.7, o perfil Salas passa também a aceitar interruptores e condições declarativas. A validação das ligações considera as condições das portas; consulta [o guia de mecanismos](events-and-mechanisms.md).

Na versão 0.8, os jogos de salas permitem gravar progresso em disco. No teste do editor, F6/F9 usam uma gravação temporária em memória, descartada ao sair do teste; consulta [o guia de gravação](saving-progress.md).

## Verificação desta entrega

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe tools\check_advanced_editor.py
```

O segundo comando altera a velocidade de um elevador e a largura de uma escada, guarda e reabre os dois documentos, e completa ambos os jogos através dos eventos de input do editor. Verifica transporte, três passagens por portas, recolha global de cristais, escada, dash e wall jumps, sem mortes. Confirma também que jogar não alterou os documentos. As imagens ficam em `artifacts/editor-rooms-completed.png` e `artifacts/editor-precision-completed.png`.
