# Quarta entrega: Ascensão

## Jogar

Abre **Jogar-Ascensao.cmd** ou executa:

```powershell
.venv\Scripts\python.exe -m examples.precision
```

A janela identifica-se como **Platform2D 0.4 - Parte 4 - Ascensao**. O percurso tem três setores e três sinais dourados para recolher:

1. **Escada:** aproxima-te da escada e mantém W ou seta para cima. No topo, caminha até ao sinal e ao checkpoint.
2. **Fosso:** aproxima-te da borda, salta para a direita e, durante o salto, prime Shift esquerdo ou C mantendo a direção. A outra margem tem um sinal e um checkpoint.
3. **Paredes:** desce ao chão e entra no espaço entre as duas paredes pela abertura inferior da parede esquerda. Salta contra a parede direita e volta a premir salto para te impulsionares para a esquerda. Alterna as paredes até chegares ao topo; salta para a plataforma final e recolhe o último sinal.

O portal do cume exige os três sinais. O percurso permite experimentar soluções alternativas: não exige uma sequência exata de capacidades para concluir.

| Comando | Resultado |
|---|---|
| A/D ou esquerda/direita | Movimento horizontal |
| W/S ou cima/baixo | Subir/descer uma escada; direção vertical do dash |
| Espaço ou Z | Salto normal, salto na parede ou saída da escada |
| Shift esquerdo ou C | Dash na direção premida; sem direção, para onde estás virado |
| Baixo + salto | Descer por plataforma unidirecional |
| R | Reaparecer no checkpoint, mantendo sinais recolhidos |
| F2 | Reiniciar todo o percurso |
| F1 | Debug com estado, colisões, escadas e contadores de capacidades |
| P / N | Pausa / uma atualização durante a pausa |

Os checkpoints são ativados por contacto. Morrer preserva os sinais da sessão. Não há gravação em disco.

## Regras das capacidades

**Dash:** oito direções, uma carga e gravidade suspensa durante o impulso. A direção fica fixa até terminar. Diagonais têm a mesma velocidade total que direções horizontais/verticais. O impulso para ao atingir um obstáculo no eixo relevante. Recarrega ao aterrar, incluindo em plataformas móveis; tocar numa parede ou agarrar uma escada não recarrega. Há uma curta recuperação após o impulso. Não concede invulnerabilidade.

**Wall jump:** requer proximidade lateral de uma parede sólida e o corpo no ar. Uma nova pressão de salto lança a personagem para o lado oposto, com um breve bloqueio da direção horizontal para evitar regressar imediatamente à parede. Manter salto aumenta a altura; largá-lo corta a subida. Encostar contra a parede enquanto cais limita a velocidade de queda. Não existe agarrar bordas nesta versão.

**Escadas:** a personagem entra ao premir cima/baixo dentro da zona. Sem input vertical permanece na escada. O alinhamento ao centro é feito por movimento com colisão. Salto ou dash permitem sair. Ao chegar ao topo ou ao chão na base, a personagem liberta a escada e pode caminhar. Escadas atravessam plataformas unidirecionais durante a subida/descida, mas continuam bloqueadas por tetos e chão sólidos. Constrói a saída superior com tiles `=` ou espaço livre.

O empurrão por dano interrompe as capacidades, sem conceder uma carga gratuita de dash. Reaparecer restaura a carga e limpa o estado de escalada.

## Reutilizar numa personagem

```python
from platform2d.actors.abilities import Abilities, PrecisionController
from platform2d.actors.character import Character
from platform2d.actors.controller import Movement
from platform2d.physics.body import Body, Box

controller = PrecisionController(
    Movement(speed=220),
    Abilities(dash=True, wall_jump=True, ladders=True),
)
player = Character(Body(64, 482), controller)
ladders = [Box(232, 320, 32, 192)]

player.update(dt, actions, colliders, moving_platforms, ladders=ladders)
```

Cada personagem deve ter a sua própria instância do controlador. Para um jogo que só precisa de escadas:

```python
controller = PrecisionController(abilities=Abilities(
    dash=False, wall_jump=False, ladders=True,
))
```

Os jogos anteriores continuam a usar `ArcadeController`, sem estas capacidades. Também podes desativar as três no controlador de precisão para comparar o comportamento.

Se usares `SpriteView`, acrescenta clips para `dash`, `climb` e `wall_slide`. Esses estados visuais não substituem `idle`, `run`, `jump` ou `fall`. A demonstração reaproveita frames da spritesheet comum; não inclui animações dedicadas de alta resolução.

## Configuração

Edita `examples/precision/settings.json` ou cria outro ficheiro e passa `--settings`. Os parâmetros de `movement` continuam a controlar o salto normal.

| Parâmetro de `abilities` | Valor inicial | Significado |
|---|---:|---|
| `dash_speed` | 650 | Unidades por segundo |
| `dash_duration` | 0.18 | Duração do impulso em segundos |
| `dash_cooldown` | 0.15 | Recuperação após terminar |
| `wall_jump_speed` | 280 | Velocidade horizontal para longe da parede |
| `wall_jump_height` | 430 | Magnitude da velocidade vertical inicial; não é altura em píxeis |
| `wall_lock` | 0.12 | Bloqueio breve de direção após o salto na parede |
| `wall_slide_speed` | 85 | Limite de queda ao pressionar contra a parede |
| `climb_speed` | 125 | Velocidade de subida/descida |

Os três interruptores `dash`, `wall_jump` e `ladders` aceitam `true`/`false`. Os parâmetros numéricos têm de ser finitos e positivos. Desativar uma capacidade pode tornar o mapa original impossível; adapta o desenho do percurso ao perfil escolhido.

## Dados do nível

O mapa está em `examples/precision/assets/ascent.json` e mantém o formato de tiles da primeira entrega. O carregador do exemplo acrescenta os tipos `ladder` e `beacon`:

```json
{"id": "ladder_a", "type": "ladder", "x": 232, "y": 320, "w": 32, "h": 192}
```

A caixa da escada é independente da imagem. A cena transforma-a numa `Box` para fornecer ao controlador. Usa `beacon` para os sinais obrigatórios, `checkpoint` para os pontos de reaparecimento e `goal` para a chegada.

O desenho e as instruções da demonstração são específicos dos três setores originais. Um novo jogo deve fornecer a sua apresentação e pode reutilizar os mesmos módulos de movimento.

## Testes e limites

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tools\check_precision_route.py
cmd /c Jogar-Ascensao.cmd --headless --frames 120 --screenshot artifacts\precision.png
```

O percurso automático só envia ações de input. Verifica o uso da escada, do dash e de pelo menos dois saltos na parede, a recolha dos três sinais e a conclusão sem mortes. Os testes incluem a normalização diagonal, paredes finas, recarga, saltos guardados na aterragem, plataformas móveis, empurrões e saídas de escadas.

Os sensores de parede usam sólidos estáticos com uma tolerância de uma unidade; não incluem paredes móveis. As escadas são retângulos verticais estáticos. O solver continua a resolver primeiro X e depois Y: o dash diagonal não é uma simulação contínua de uma trajetória diagonal arbitrária. Não existem agarrar bordas, natação, cordas, recarga ao tocar em paredes ou dash com invulnerabilidade.

`tools/build_precision_map.py` reconstrói **e substitui** o mapa original. Guarda mapas próprios com outro nome. O teste de percurso depende da geometria original.
