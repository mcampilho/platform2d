# Transições entre momentos

`platform2d.rendering.transition` inclui dois controladores independentes da lógica do jogo.

`FadeTransition` cobre uma mudança de sala e executa a função de troca uma única vez, no ponto em que o ecrã está totalmente escuro. `MomentTransitions` apresenta sinais breves para a entrada numa cena, a ativação de um checkpoint e a conclusão de um nível:

```python
from platform2d.rendering.transition import MomentTransitions

transitions = MomentTransitions()
transitions.enter()

# No ciclo de atualização:
transitions.update(dt)

# Depois de desenhar o mundo e antes da interface principal:
transitions.draw(surface)
```

Usa `transitions.checkpoint((x, y))` com coordenadas do ecrã para produzir uma onda local a partir do ponto alcançado. O desenho fica limitado à área da onda para preservar a fluidez. Usa `transitions.complete()` quando os objetivos terminarem. Uma nova indicação substitui naturalmente a anterior, evitando a acumulação de camadas.

Para a opção de efeitos reduzidos, define `transitions.enabled = False` e chama `transitions.clear()`. As transições são apenas visuais: não param o relógio, não alteram a física e não executam ações de jogo.

A campanha demonstra os três momentos. A entrada ou o reaparecimento revelam a cena, o checkpoint emite uma onda suave e a conclusão introduz barras cinematográficas atrás do painel de resultados.
