# Segunda entrega: salas, portas e plataformas móveis

## Executar e experimentar

Abre `Jogar Salas.cmd` ou executa `python -m examples.rooms` com o ambiente do projeto ativo. Os comandos de movimento são os mesmos da primeira demonstração; **E** ou **seta para cima** atravessam uma porta quando a indicação aparece.

No átrio, recolhe o cristal junto ao chão, espera pelo elevador e salta para o seu topo. Deixa-o subir e passa para o piso superior. A porta do lado direito leva à galeria. O checkpoint fica perto da entrada; salta para a plataforma horizontal quando esta se aproxima e deixa-te transportar. O núcleo à direita exige os quatro cristais das duas salas.

Podes regressar ao átrio pela porta da esquerda. Os cristais recolhidos permanecem recolhidos. Uma sala vazia fica suspensa, pelo que as plataformas retomam a posição em que estavam quando saíste.

- **R:** regressar ao checkpoint, mesmo que fique noutra sala.
- **F2:** limpar a sessão completa: cristais, checkpoint e fases das plataformas.
- **P / N:** pausar e avançar uma atualização. A pausa também congela plataformas e transições.
- **F1:** grelha e informações da personagem e da sala.
- **F6 / F9:** guardar/carregar progresso desde a versão 0.8; consulta [o guia de gravação](saving-progress.md). F2 não apaga o ficheiro guardado.

## Estrutura do mundo

O ficheiro `examples/rooms/assets/world.json` contém:

```json
{
  "version": 1,
  "start_room": "atrium",
  "start_entry": "start",
  "rooms": {
    "atrium": { "version": 1, "name": "Átrio", "tile_size": 32, "tiles": [], "objects": [] },
    "archive": { "version": 1, "name": "Arquivo", "tile_size": 32, "tiles": [], "objects": [] }
  }
}
```

O exemplo acima ilustra apenas a estrutura: as listas `tiles` e `objects` precisam de ser preenchidas. Cada sala usa o formato de mapa da primeira entrega e deve conter exatamente um `spawn`. O jogo de exemplo exige mapas 30×18 com tiles de 32, correspondendo à janela 960×576. O gestor `RoomWorld` não impõe esse tamanho; é uma escolha da apresentação do exemplo.

Os IDs de objetos têm de ser únicos **dentro de cada sala**. As salas podem reutilizar o mesmo ID sem partilhar estado.

## Entradas e portas

Uma entrada é uma posição de chegada, com o canto superior esquerdo do corpo em `x`, `y`:

```json
{"id": "from_atrium", "type": "entry", "x": 112, "y": 482}
```

O objeto `spawn` também pode ser usado como entrada. O carregador verifica que existe espaço para o corpo padrão 24×30 nas entradas.

Uma porta referencia explicitamente uma sala e uma entrada:

```json
{
  "id": "to_archive", "type": "door",
  "x": 884, "y": 454, "w": 32, "h": 58,
  "target_room": "archive", "target_entry": "from_atrium",
  "label": "ARQUIVO"
}
```

As referências são verificadas quando o mundo é carregado. A ligação de regresso é outra porta: não é criada implicitamente. Coloca a entrada afastada da porta de regresso para tornar a chegada mais clara.

## Plataformas móveis

```json
{
  "id": "lift", "type": "moving_platform",
  "x": 288, "y": 480, "w": 96, "h": 12,
  "end": [288, 288], "speed": 48
}
```

`x`, `y` são o início; `end` é o destino. A plataforma vai e volta, a velocidade constante em unidades/segundo. Os dois pontos têm de ser diferentes e o percurso deve ficar dentro da sala. A mesma classe aceita trajetos horizontais, verticais ou diagonais em linha reta. Não há pausas nos extremos nesta versão.

O topo transporta o passageiro; laterais e fundo são atravessáveis. Baixo + salto permite descer pelo topo. Se o elevador comprimir o passageiro contra um teto estático, o motor assinala esmagamento; neste exemplo, a personagem reaparece no checkpoint.

O autor deve manter percursos livres de geometria incompatível: as plataformas são cinemáticas e não param ao tocar nas paredes. Não há colisão entre plataformas, empurrão lateral, esmagamento entre máquinas nem herança de velocidade no salto. Essas situações exigem regras adicionais antes de serem usadas em níveis.

## Reutilizar no teu jogo

```python
world = RoomWorld.load("world.json")
player.respawn(world.respawn())

# Uma atualização de simulação:
room = world.current
room.update(dt)  # exatamente uma vez; antes de atualizar os passageiros
player.update(dt, actions, room.level.colliders, room.platforms)

# Trocar de sala:
position = world.enter("archive", "from_atrium")
player.respawn(position)

# Remover um objeto sem modificar a definição do nível:
world.current.state.removed.add("crystal_1")

# Guardar um checkpoint na sessão:
world.set_checkpoint((146, 482))
```

Importa `RoomWorld` de `platform2d.world.room`. A escolha de quando interagir, morrer, guardar ou concluir continua a pertencer à cena do jogo. O gestor disponibiliza estado, não impõe regras de pontuação.

O segundo exemplo partilha a spritesheet de explorador da primeira demonstração, mas tem cena, configuração e mapa próprios. A lógica da personagem não foi duplicada.

## Editar e testar

Duplica o JSON para outro nome e executa:

```powershell
.venv\Scripts\python.exe -m examples.rooms --world caminho\outro-mundo.json
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tools\check_rooms_route.py
```

`tools/build_rooms_map.py` reconstrói **e substitui** apenas o mapa original do Arquivo Lunar. Não o uses para guardar alterações manuais. O teste de percurso usa o mapa original e os seus pontos de passagem; mapas diferentes precisam de um percurso de teste próprio.

A persistência desta entrega é apenas em memória: fechar o jogo termina a sessão. O formato mantém `version: 1`, pois o mapa original continua compatível; a versão do pacote passa a `0.2.0`.
