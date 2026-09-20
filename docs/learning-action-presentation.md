# Aprender com a fase 0.21: desenhar a ação sem controlar as regras

O princípio desta fase é separar o que acontece no jogo da forma como o mostramos. Um ataque já tinha preparação, janela ativa e recuperação; agora cada intervalo tem uma pose legível.

## 1. Ler o estado existente

Começa em `platform2d/rendering/action_pose.py`, na função `sword_pose`. Esta lê `Sword` e `Health` e devolve uma fase e o progresso dentro dela. Não avança relógios nem aplica dano. A janela ativa vem de `Attack.active`, incluindo a deteção de intervalos atravessados entre dois passos da simulação.

O dano recente tem prioridade visual, seguido da vulnerabilidade, defesa e ataque. Passado o breve sinal de dano, uma personagem ainda atordoada volta à pose vulnerável. Isto permite comunicar duas situações sucessivas sem mudar os tempos do combate.

## 2. Construir uma figura articulada

`draw_actor` usa coordenadas locais para pés, tronco, capacete, braços e espada. A função interna `point` transforma essas coordenadas em posições do ecrã e espelha a figura quando muda de direção. A inclinação do tronco e os pontos do braço variam com a fase; a silhueta explica a ação mesmo sem depender apenas da cor.

No transporte, as mãos sobem e a função termina antes de desenhar uma espada. `AdventureScene.rocket_draw` coloca a carga acima das mãos. Ambos usam `Body.interpolated(alpha)`, a posição visual entre dois passos da física.

## 3. Integrar por um ponto de extensão

Em `examples/ranged/scene.py`, `draw_world` chama agora `draw_player`. A implementação base conserva o sprite existente. `AdventureScene` especializa apenas o transporte; `DuelScene` especializa o desenho de espada. Assim, uma cena pode mudar o aspeto do jogador sem copiar todo o desenho do mundo ou alterar a física.

As marcas de impacto são criadas quando o combate confirma o resultado. A sua duração diminui em `update_encounters`, nunca em `draw`. Desenhar dez vezes o mesmo instante não acelera nem o golpe nem o desaparecimento do efeito. A pausa funciona porque não avança essa atualização.

## 4. Experimentar uma alteração pequena

Experimenta mudar a inclinação de `windup` ou a cor da lâmina. Executa os testes e compara a preparação do golpe. O alcance real permanece em `AttackSpec`: aumentar apenas o desenho da espada não deve aumentar a zona de dano. Para evitar uma indicação enganadora, a pose de golpe recebe o alcance real como argumento.

Executa, na pasta do projeto:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_action_presentation.py
.venv\Scripts\python.exe tools\check_action_presentation.py
.venv\Scripts\python.exe tools\check_duel.py
```

Os testes verificam a separação entre apresentação e simulação. A folha de poses permite avaliar a leitura visual; o percurso do duelo verifica que as ações continuam a produzir o resultado esperado. São verificações complementares.
