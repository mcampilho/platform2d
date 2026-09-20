# Sétima entrega — Central de Energia

## Experimentar

Abre **Jogar-Mecanismos.cmd** para jogar ou **Editor-Mecanismos.cmd** para editar uma cópia do novo mundo. Este modelo usa o perfil **Salas**, agora com interruptores e condições; não é um quarto perfil.

Na Central de Energia:

1. Na primeira sala, ativa **Alimentação** com E. A porta REATOR fica disponível. Recolhe o cristal.
2. Usa E junto à porta. Na segunda sala, passa pelo **Sensor de presença**, que fica ativado ao tocar nele.
3. A **Consola do reator** exige Alimentação e Sensor de presença. Ativa-a com E.
4. Recolhe o segundo cristal e chega à saída. A saída exige todos os cristais e a consola ativa.

Podes experimentar a porta antes de ativar Alimentação, ou a saída antes da consola: a mensagem indica o que falta. Portas indisponíveis usam uma cor âmbar e um pequeno cadeado. Interruptores ativos ficam verdes.

**R** regressa ao checkpoint e conserva cristais e mecanismos. Morrer também os conserva. **F2** reinicia toda a partida, incluindo os interruptores. Desde a versão 0.8, **F6 guarda** e **F9 carrega** o progresso em disco; no Atelier, usam apenas memória. Consulta [guardar e retomar uma partida](saving-progress.md).

## Criar mecanismos no Atelier

As ferramentas estão disponíveis em qualquer projeto do perfil **Salas**, incluindo mundos antigos.

### Interruptor

1. Usa **T — Interruptor** e coloca o objeto.
2. Seleciona-o e clica em **Configurar interruptor…**.
3. Altera o nome apresentado no jogo.
4. Escolhe a ativação: **tecla E** (por proximidade) ou **ao tocar** (contacto com a área W/H).
5. Opcionalmente, define condições que devem estar cumpridas antes de o interruptor aceitar a ativação.

Cada interruptor só ativa uma vez por partida. Um sensor por contacto também permanece ativo depois de o jogador sair: não é uma placa que precise de peso contínuo. Ainda não há interruptores que alternem entre ligado/desligado, temporizadores ou lógica OR/NOT.

### Porta ou saída condicionada

Seleciona a porta e abre **Destino / condições…**. **Ligar porta…** conserva o seletor de sala e entrada da entrega anterior; **Condições de abertura…** define os interruptores necessários.

Na saída final, usa **Condições da saída…**. A saída continua a exigir todos os cristais do mundo, além das condições escolhidas.

No diálogo das condições:

- **Adicionar condição** mostra interruptores existentes em todas as salas, identificados por sala e ID, com o nome apresentado no jogo.
- Todos os interruptores da lista têm de estar ativos (**AND**).
- Clicar numa condição remove-a. A alteração pode ser desfeita com Ctrl+Z.
- Sem condições, o objeto está sempre disponível, mantendo o comportamento anterior.
- Um ponto âmbar no canto do objeto, no mapa, indica que tem condições.

Mudar o ID de uma sala ou de um interruptor atualiza as referências em todo o mundo. Eliminar um interruptor conserva as referências quebradas para que F8 as identifique; corrige-as antes de guardar/testar. As condições são guardadas no mesmo JSON do mundo.

E escolhe **um único objeto**, o mais próximo dentro da área de interação. Em caso de empate, usa o ID para uma ordem estável. Interruptores já ativos não competem com portas. Evita sobrepor objetos interativos se quiseres uma escolha evidente para o jogador.

As portas desta entrega são passagens entre salas: a condição bloqueia a passagem ao premir E. Não são barreiras físicas que colidam com o jogador.

## Validação

F8 conserva as verificações geométricas e das ligações e acrescenta:

- Referências a interruptores inexistentes: **erro**, com localização do objeto que depende deles.
- Área de ativação de um interruptor totalmente bloqueada por sólidos/perigos: **erro**.
- Condições bloqueadas por ciclos ou por interruptores atrás de portas fechadas: **aviso** no objeto afetado.
- Cristais obrigatórios em salas que não podem ser abertas, nenhuma saída ligada, ou todas as saídas finais dependentes de interruptores impossíveis de ativar nesse modelo: **erro**.

A análise parte da sala inicial. Considera todos os interruptores geometricamente acessíveis dentro de cada sala atingida, ativa os que têm condições satisfeitas e atravessa as portas disponíveis. Repete até deixar de haver alterações. Esta aproximação é deliberadamente generosa: ignora saltos, obstáculos, plataformas móveis e a necessidade de uma única rota física. **Não é uma confirmação de solução jogável.** Uma dependência opcional bloqueada pode produzir apenas um aviso, se não impedir os objetivos obrigatórios.

Ficheiros com estrutura inválida de condições, referências repetidas no mesmo objeto ou modos de ativação desconhecidos são rejeitados ao abrir, com uma mensagem. F5 inicia uma cópia isolada; os mecanismos ativados durante o teste não ficam gravados no documento.

## Dados e módulos reutilizáveis

O formato mantém `version: 1`. O novo objeto `switch` aceita `activation: "interact"` (predefinição) ou `"touch"`, `label` e as dimensões habituais. Portas, saídas e interruptores podem conter:

```json
"requires": [
  {"room": "control", "switch": "power"},
  {"room": "reactor", "switch": "sensor"}
]
```

As referências usam IDs, não os nomes visíveis. Mundos sem `switch` ou `requires` mantêm as regras anteriores. Condições não são suportadas nos perfis Clássico e Precisão.

`platform2d.core.events` fornece `Event` e `EventBus`, sem dependência de Pygame. `subscribe(kind, callback)` devolve uma função para cancelar a subscrição; `publish(event)` notifica uma cópia da lista atual de ouvintes, sincronamente. Exceções dos ouvintes são propagadas ao anfitrião.

`platform2d.gameplay.mechanisms.Mechanisms` conserva as ativações e verifica condições. `activate(room_id, obj)` devolve `True` e publica **switch_activated** apenas na primeira ativação válida. A origem do evento é `(room_id, switch_id)`. O estado já está atualizado quando os ouvintes são chamados. `reset()` limpa ativações, conservando subscrições.

```python
stop = world.mechanisms.events.subscribe(
    "switch_activated", lambda event: print(event.source)
)
# O jogo pode reagir com áudio, efeitos ou regras próprias.
stop()  # retirar o ouvinte
```

O JSON não executa código: esta entrega oferece mecanismos declarativos e notificações, não uma linguagem de scripting geral. O estado pertence a `RoomWorld`, separado das definições e da apresentação da cena. Ao tocar num perigo, o dano tem prioridade sobre mecanismos e objetivos naquele passo.

## Verificar

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe tools\check_mechanisms_route.py
.venv\Scripts\python.exe -m examples.mechanisms --headless --frames 3 --screenshot artifacts\mechanisms.png
```

O percurso automático guarda/reabre o mundo e usa eventos de teclado no editor. Verifica a porta inicialmente bloqueada, três ativações (uma por contacto), a saída condicionada, três passagens entre salas, preservação ao usar R, reinício por F2 e documento intacto no regresso à edição. Completa sem mortes. Os testes unitários verificam também preservação após morte, ciclos, referências inválidas, renomeação, histórico e edição visual das condições.
