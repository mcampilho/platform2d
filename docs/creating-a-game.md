# Criar uma segunda sala e alterar os controlos

## Duplicar o mapa

Copia `examples/classic/assets/station.json` para `examples/classic/assets/my-room.json`. Mantém `version: 1`, um `tile_size` inteiro positivo e linhas de `tiles` com a mesma largura.

| Símbolo | Superfície |
|---|---|
| `.` | Vazio |
| `#` | Sólido |
| `=` | Plataforma unidirecional; superfície no topo do tile |

As imagens e as colisões são separadas: o mapa contém a geometria lógica e a cena escolhe a aparência. Esta primeira versão usa uma camada de tiles e uma lista de objetos; não existe ainda suporte a camadas visuais independentes ou TMX.

Um exemplo mínimo completo:

```json
{
  "version": 1,
  "name": "Sala de teste",
  "tile_size": 32,
  "tiles": [
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..............................",
    "..........====................",
    "..............................",
    "..............................",
    "##############################",
    "##############################",
    "##############################"
  ],
  "objects": [
    {"id": "start", "type": "spawn", "x": 64, "y": 418},
    {"id": "crystal", "type": "coin", "x": 350, "y": 320},
    {"id": "exit", "type": "goal", "x": 860, "y": 390, "w": 32, "h": 58}
  ]
}
```

Executa a nova sala sem alterar código:

```powershell
.venv\Scripts\python.exe -m examples.classic --map examples/classic/assets/my-room.json
```

As coordenadas de objetos são unidades de mundo, não índices de tiles. Cada objeto tem um ID único. É obrigatório existir exatamente um `spawn`. Tipos adicionais: `checkpoint` e `hazard`. A cena atribui a área padrão 24×30 quando `w` e `h` são omitidos. Coloca spawn e checkpoints fora dos sólidos, com espaço para um corpo 24×30. A validade geométrica desses pontos é responsabilidade do autor nesta versão.

O portal só abre depois de recolher todos os objetos `coin` da sala. Um mapa sem cristais permite entrar diretamente no portal.

## Alterar o movimento

Edita `examples/classic/settings.json`. `jump_speed` é uma magnitude positiva; o controlador aplica o sinal negativo ao saltar.

- `speed`: velocidade horizontal máxima.
- `acceleration` / `friction`: rapidez a acelerar / travar.
- `gravity` / `jump_speed`: forma geral do salto.
- `jump_cut`: limite de velocidade ascendente após largar salto.
- `air_control`: multiplicador de aceleração e travagem no ar.
- `coyote_time` / `jump_buffer`: tolerâncias em segundos.

Experimenta `speed: 180`, `jump_speed: 400` e `gravity: 1100` para um movimento mais lento. Configurações diferentes podem tornar o percurso original impossível: testa o alcance antes de desenhar o nível.

As listas em `bindings` usam nomes de teclas do Pygame, por exemplo `space`, `left`, `a` e `z`. Podes ter várias teclas para uma ação. O HUD desta demonstração é fixo e deve ser adaptado se trocares as teclas. Para guardar perfis distintos, cria outro JSON e usa `--settings caminho/do/perfil.json`.

## Criar um jogo separado

Cria outro módulo dentro de `examples/`, implementa o contrato `Scene` e passa uma instância a `Game`. Reutiliza `Character`, `TileMap`, `Camera` e `SpriteView`; coloca regras, HUD e recursos no módulo do teu jogo.

Para usar outra spritesheet, carrega uma imagem com `pygame.image.load`, divide-a com `slice_sheet` e define clips com índices de frames. Os frames têm tamanho uniforme e são lidos da esquerda para a direita, de cima para baixo. O tamanho da imagem não precisa de coincidir com a hitbox; define o deslocamento ao desenhar.


## Superfícies inclinadas (0.11.0)

A grelha aceita rampas / e barra invertida, de 45° e atravessáveis por baixo. Os colisores descrevem a inclinação e o motor resolve as transições com o chão plano. Mapas sem rampas mantêm o algoritmo anterior. Consulta [rampas e terreno](slopes-and-terrain.md) para formato, integração, limites e validação.


## Projéteis (0.12.0)

`Weapon` controla a cadência, `ProjectileSystem` move tiros e emite impactos, e a cena aplica dano e efeitos. O perfil Combate usa `properties.weapon` e os objetos `target`/`turret`. O núcleo de projéteis não depende do Pygame. Consulta [projéteis e combate](projectiles-and-ranged-combat.md) e o [guia de aprendizagem desta fase](learning-projectiles.md).
