# Aprender com a fase 18

Experimenta primeiro **Jogar-Duelo.cmd**: observa o Guardião preparar o golpe, defende no momento certo e responde com a espada. Depois acompanha estas quatro camadas.

## 1. A janela de ataque continua reutilizável

`platform2d/gameplay/combat.py` já tinha `Attack` e `AttackSpec`. Aproveitamos a mesma preparação, janela ativa, recuperação e registo de alvos atingidos. O desenho da espada não decide quando causa dano. Um alvo só pode ser atingido uma vez por golpe; a linha entre atacante e alvo também é testada contra paredes.

O jogador usa 0,16 s de preparação, 0,12 s de atividade e 0,32 s de recuperação. O Guardião prepara durante 0,55 s e recupera durante 0,85 s. Esta assimetria dá tempo para aprender a reconhecer o ataque.

## 2. A defesa decide um resultado

`platform2d/gameplay/sword.py` compõe `Attack` com resistência, defesa e interrupção. `defend()` devolve `hit`, `block`, `parry` ou `break`. Não toca áudio, não desenha e não escolhe o próximo nível. A cena recebe o resultado e aplica dano, mensagem ou vulnerabilidade.

A defesa só protege a frente do corpo. A janela curta ao iniciar a defesa recompensa o momento da ação; a drenagem de resistência limita a defesa contínua. Uma interrupção cancela imediatamente a janela de ataque, evitando golpes que continuassem ativos após um desvio.

## 3. O adversário escolhe ações

`Guardian`, em `examples/campaign/duel.py`, aproxima-se com um `Character` normal. Quando chega ao alcance, espera em guarda, prepara um golpe e recupera. Usa as mesmas colisões, o mesmo objeto `Sword` e o mesmo sistema `Health` que o jogador.

A cena `DuelScene` resolve o combate no ponto `update_encounters()` da cena base, depois do movimento e antes da morte/saída. Isto garante que derrotar o adversário e verificar o objetivo fazem parte do mesmo passo de simulação. A IA e a apresentação continuam no exemplo; a defesa permanece reutilizável no motor.

Na ordem de resolução atual, o ataque do jogador é resolvido primeiro. Um golpe ou desvio que interrompa o inimigo cancela a resposta desse passo. Esta prioridade é deliberada e não uma simulação física de espadas.

## 4. Progresso permanente versus estado momentâneo

O ID do Guardião derrotado entra no conjunto `destroyed`, já usado pela campanha. A validação da vitória exige agora também derrotar os objetos `guardian`. A retoma recria apenas os adversários vivos; não serializa temporizadores de ataque nem posições transitórias.

A nova campanha referencia os sete mapas anteriores e acrescenta um oitavo. Um manifesto diferente produz uma gravação independente, permitindo conservar o progresso anterior.

## A melhoria do foguetão

`RocketMission.part_order` segue a ordem das peças na lista `objects`. `next_part` calcula a primeira ainda em falta. Só essa peça pode ser recolhida, evitando ficar preso a transportar uma peça que ainda não pode ser instalada.

`platform2d/rendering/rocket.py` desenha motor, depósito e cockpit com silhuetas distintas. A mesma função desenha a peça no mapa e nas mãos. O combustível é uma fração calculada a partir das entregas; uma máscara restringe a cor âmbar à silhueta da nave, e um recorte faz a cor subir desde a base. O estado do jogo nunca depende da cor dos píxeis.

Experimenta mudar os tempos em `AttackSpec`, repetir o duelo e observar a diferença entre dificuldade e falta de tempo para reagir. Usa os testes isolados e o percurso completo para verificar que as alterações continuam justas e jogáveis.
