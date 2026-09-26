# Orientação para objetivos

`platform2d.rendering.guidance.ObjectiveGuide` apresenta uma seta discreta na margem do ecrã quando um ponto importante está fora da área visível. O indicador desaparece assim que o ponto entra no ecrã e não modifica a câmara, a física ou o estado da missão.

```python
from platform2d.rendering.guidance import ObjectiveGuide

guide = ObjectiveGuide(color=(132, 229, 214))
point = world_to_screen(objective_position)
guide.draw(screen, point, viewport=(0, 96, 960, 459), age=elapsed)
```

Passa `reduced=True` para conservar a direção sem a pequena pulsação. O jogo deve escolher apenas informação que o jogador já conhece: a saída depois de cumprir os requisitos ou o objetivo obrigatório mais próximo. Não marques interruptores ocultos, combinações ou posições que constituam a solução de um puzzle.

A campanha usa esta orientação nos níveis com scroll. Cristais, alvos e capacidades obrigatórias têm prioridade; depois de concluídos, a indicação passa para a saída. Plataformas, placas, caixas e mecanismos não são assinalados.
