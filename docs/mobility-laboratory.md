# Laboratório de mobilidade

Executa `Jogar-Mobilidade.cmd` ou, na raiz do projeto, `python -m examples.mobility`.
O percurso usa as mesmas regras físicas dos outros exemplos de precisão. Divide-se em cinco zonas com instruções no topo do ecrã: salto tolerante, dash, salto na parede, salto duplo e glide. Os checkpoints permitem repetir cada zona sem voltar ao início. F2 reinicia todo o percurso; R reaparece no último checkpoint.

Move-te com A/D ou as setas. Espaço/Z salta, Shift esquerdo/C faz dash, X permite planar enquanto cais. P pausa e F1 mostra a geometria e o estado físico.

Em `examples/mobility/settings.json`, `movement.coyote_time` define quanto tempo ainda se pode saltar após sair de uma plataforma; `movement.jump_buffer` define durante quanto tempo uma pressão antecipada aguarda pela aterragem. Os restantes parâmetros de `movement` controlam a velocidade, aceleração, gravidade e altura do salto. Na secção `abilities`, os interruptores `dash`, `wall_jump`, `double_jump` e `glide` aceitam `true` ou `false`. `glide_fall_speed` limita a velocidade de descida enquanto X está premido. O salto duplo só recarrega ao tocar no chão; o dash também segue a sua regra de recarga existente.

Para experimentar outra combinação sem mudar o ficheiro original, copia as definições e executa:

```powershell
python -m examples.mobility --settings minhas-definicoes.json
```

O mapa está em `examples/mobility/assets/laboratory.json`. Podes passar outro ficheiro com `--map`. `properties.lessons` contém as instruções de cada zona: `x` é a posição horizontal a partir da qual a mensagem aparece, `title` é o nome da mecânica e `help` explica a ação. O percurso usa os objetos `spawn`, `checkpoint` e `goal` do formato normal de mapas. Uma alteração às capacidades pode tornar um obstáculo impossível; adapta a geometria ao conjunto escolhido.

Para integrar as capacidades no teu jogo, cria um `PrecisionController` com `Movement(...)` e `Abilities(double_jump=True, glide=True, ...)`. O teu ciclo de atualização continua a chamar `Character.update(dt, actions, colliders)`. Associa a ação `glide` a uma tecla ou botão e fornece o estado `held` enquanto esse controlo estiver premido. Os controladores antigos mantêm os valores por defeito (`double_jump=False`, `glide=False`).
