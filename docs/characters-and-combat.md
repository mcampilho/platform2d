# Terceira entrega: Sentinelas

## Jogar

Abre **Jogar-Sentinelas.cmd** ou executa:

```powershell
.venv\Scripts\python.exe -m examples.sentinels
```

O lançador não contém espaços. A janela deve indicar **Platform2D 0.3 - Parte 3 - Sentinelas**.

1. Aproxima-te de Íris, junto à entrada, e prime **E**. Avança as três falas com novas pressões de E.
2. Aproxima-te dos guardas e usa **J** ou **X**. Cada um tem dois pontos de vida; cada golpe causa um de dano. É preciso voltar a premir para iniciar outro golpe.
3. Depois de derrotar os dois guardas, usa **E** junto ao terminal amarelo do lado direito.
4. A barreira abre; atravessa a saída.

O jogador tem três pontos de vida. O contacto com um guarda causa dano, empurrão e 0,9 segundos de invulnerabilidade, assinalados pelo piscar da personagem. Durante a recuperação do empurrão não podes iniciar um golpe. A vida não regenera automaticamente.

**R** regressa ao início e recupera vida. Os guardas já derrotados, a conversa e a abertura do terminal mantêm-se durante a sessão. Guardas ainda vivos regressam à posição e vida iniciais. **F2** limpa todo o progresso. **P** pausa; **N** avança uma atualização em pausa. O diálogo também suspende a simulação, permitindo ler sem receber ataques.

## O que observar no debug

Com **F1**, os cones translúcidos indicam o alcance e a orientação de cada guarda. O cone representa o campo potencial e não é recortado pelos obstáculos. Uma linha até ao jogador aparece apenas quando a visão real está confirmada. Blocos sólidos interrompem essa visão; plataformas finas não.

Os rótulos dos guardas distinguem patrulha, alerta, procura e dano. Depois de perderem o jogador de vista, continuam brevemente para a última posição vista, param para procurar e retomam a patrulha. Não conhecem automaticamente a posição atual de um jogador escondido.

## Máquina de estados reutilizável

```python
from platform2d.actors.state_machine import State, StateMachine

states = {
    "idle": State(enter=lambda actor: actor.stop()),
    "walk": State(update=lambda actor, dt: actor.walk(dt)),
}
machine = StateMachine(actor, states, "idle")
machine.change("walk")
machine.update(1 / 60)
```

Os hooks recebem o objeto dono da máquina. `machine.current` identifica o estado e `machine.elapsed` o tempo passado nele. Os hooks `enter` e `exit` são opcionais. Faz transições na lógica de atualização ou por eventos externos, não dentro de `enter` ou `exit`.

A máquina dos guardas usa cinco estados: `patrol`, `chase`, `search`, `hurt` e `dead`. Os estados de animação/locomoção da personagem continuam separados.

## Vida e ataque

```python
from platform2d.gameplay.combat import Health, Attack, AttackSpec

health = Health(maximum=3, invulnerability=0.9)
health.update(dt)
if health.hit(1):
    player.knockback(-210, vy=-160, duration=0.18)

attack = Attack(AttackSpec(startup=0.08, active=0.10, recovery=0.22,
                         reach=42, damage=1))
attack.start(facing=1)
attack.update(dt)
if attack.connects(enemy.id, player.body, enemy.body.box, colliders):
    enemy.hit(attack.spec.damage, attack.facing)
```

Mantém a mesma instância de ataque entre atualizações; não a recries por frame. `start` devolve `False` se o golpe anterior ainda está em curso. A direção fica fixada ao iniciar. `connects` só funciona na janela ativa e regista cada alvo uma vez por golpe. A lista de colisores impede atingir um alvo através de um sólido. Ao iniciar outro golpe, a lista de alvos atingidos é limpa.

O ataque da demonstração é uma emissão curta retangular, desenhada separadamente do sprite. Não é uma animação de espada. Hurtboxes alternativas podem ser fornecidas como `Box`; não é obrigatório coincidir com a colisão do corpo. Defesa, combos, projéteis e marcadores de animação ficam para extensões futuras.

## Interação contextual

```python
from platform2d.gameplay.interaction import Interaction, choose_interaction

actions = [
    Interaction("iris", "Falar", (154, 497), open_dialogue, radius=60),
    Interaction("console", "Ativar", (850, 495), open_gate, radius=55, priority=1),
]
selected = choose_interaction(player.body, actions)
if selected and "interact" in input_actions.pressed:
    selected.callback()
```

O seletor filtra ações desativadas e fora do raio, escolhe a maior prioridade e depois a menor distância. Empates usam o ID. As posições referem-se ao ponto de interação, comparado com o centro do corpo. A cena decide as condições de validade: permissões, paredes e requisitos de missão não são inferidos pelo seletor.

Em Sentinelas, o diálogo é linear e o terminal exige a conversa concluída e todos os guardas derrotados. Não existe um sistema genérico de missões ou árvores de diálogo nesta entrega.

## Mapas e configuração

O mapa é `examples/sentinels/assets/outpost.json`; as teclas e os parâmetros de movimento estão em `examples/sentinels/settings.json`. Usa `--map` e `--settings` para carregar cópias próprias.

Um inimigo no mapa:

```json
{
  "id": "guard_1", "type": "enemy", "x": 400, "y": 482,
  "left": 300, "right": 478, "facing": -1
}
```

`left` e `right` delimitam a patrulha horizontal usando o canto esquerdo do corpo. A perseguição pode sair desses limites; a patrulha tenta regressar. A direção é `-1` para a esquerda e `1` para a direita. A inteligência artificial evita bordas, mas não planeia saltos, não sobe escadas e não procura caminhos entre salas. O empurrão pode lançá-la de uma borda; mapas que usem fossos devem acrescentar a respetiva regra de morte/reaparecimento dos inimigos.

O exemplo espera exatamente um `npc`, um `switch`, um `gate` e um `goal`, num mapa de 960×576. O seu texto foi escrito para dois guardas. Outros jogos podem reutilizar os módulos sem essas restrições. O desenho do NPC, diálogo, missão e terminal pertence ao exemplo; o motor fornece o movimento e as primitivas de comportamento.

## Verificar

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tools\check_sentinels_route.py
cmd /c Jogar-Sentinelas.cmd --headless --frames 120 --screenshot artifacts\sentinels.png
```

O percurso automático usa apenas ações de input: não teletransporta o jogador nem altera diretamente a vida dos guardas. Os testes de unidade incluem obstáculos na visão, memória de perseguição, bordas, dano, invulnerabilidade, janelas de ataque, prioridade de interação e persistência após reaparecer.

`tools/build_sentinels_map.py` reconstrói **e substitui** o mapa original. Guarda alterações pessoais num ficheiro diferente. A versão do pacote é `0.3.0`; os dois exemplos anteriores permanecem disponíveis.
