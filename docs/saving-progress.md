# Oitava entrega — guardar e retomar uma partida

## Usar

A gravação está disponível nos jogos **Arquivo Lunar** (`Jogar Salas.cmd`) e **Central de Energia** (`Jogar-Mecanismos.cmd`), incluindo mundos personalizados do perfil Salas.

| Comando | Resultado |
|---|---|
| F6 | Guarda o progresso atual |
| F9 | Carrega a última gravação compatível e retoma no checkpoint |
| R | Regressa ao checkpoint da sessão atual; não lê nem escreve ficheiros |
| F2 | Reinicia a sessão; conserva a gravação em disco |

Para experimentar: ativa Alimentação, recolhe o primeiro cristal, entra no reator, passa pelo checkpoint e pelo sensor. Prime **F6**, fecha o jogo, abre-o novamente e prime **F9**. Apareces no checkpoint do reator, com o cristal e os interruptores conservados.

O jogo **não carrega nem guarda automaticamente**. Ao abrir começa uma nova sessão, e F9 recupera a gravação. F6 substitui a gravação anterior compatível desse ficheiro. Após F2 podes recuperar a partida anterior com F9; se premisses F6 entretanto, guardarias a nova sessão.

## O que é conservado

- Sala e posição do último checkpoint; antes do primeiro checkpoint usa-se a entrada inicial do mundo.
- Cristais recolhidos em todas as salas.
- Interruptores ativos, sem voltar a emitir os eventos de ativação ao carregar.
- Último indicador de checkpoint de cada sala.
- Fase de movimento das plataformas de todas as salas.
- Número de mortes, tempo de jogo e estado de conclusão.

O carregamento retoma **no checkpoint**, não na posição exata onde premiste F6. Velocidade, salto e outros movimentos em curso são reiniciados. Se a partida estava concluída, continua a mostrar a conclusão; F2 permite recomeçar.

F6/F9 funcionam também em pausa e no ecrã de conclusão. Carregar retira a pausa. Durante uma transição entre salas, o pedido é recusado com uma mensagem; espera pela passagem e prime a tecla novamente.

Esta entrega não grava Clássico, Precisão ou Sentinelas. Não inclui vários espaços de gravação na interface, autosave nem migração de partidas entre versões diferentes de um mapa.

## Onde ficam os ficheiros

Os lançadores usam a pasta do projeto. As gravações predefinidas são:

- `saves/arquivo-lunar.progress.json`
- `saves/central-energia.progress.json`

A pasta só é criada quando guardas pela primeira vez. Os ficheiros de progresso são separados dos mapas em `levels/` e dos recursos em `examples/`. `saves/` está excluída do controlo de versões.

Com `--world`, o nome predefinido é `saves/world-<identificador>.progress.json`, calculado a partir do caminho absoluto do mundo. Dois mapas em caminhos diferentes têm ficheiros separados; editar o mapa no mesmo caminho mantém o destino, permitindo detetar a incompatibilidade. Mover/renomear o mapa altera esse nome predefinido.

Podes escolher um ficheiro explicitamente, por exemplo para conservar outra partida:

```powershell
.venv\Scripts\python.exe -m examples.mechanisms --save-file saves\central-alternativa.progress.json
.venv\Scripts\python.exe -m examples.rooms --world levels\meu-mundo.json --save-file saves\meu-mundo.progress.json
```

Ao executar diretamente noutra pasta, caminhos relativos usam essa pasta. Não uses o próprio mapa como ficheiro de progresso: o programa rejeita essa utilização e a gravação também recusa substituir ficheiros que não sejam progresso válido.

## Compatibilidade e falhas

A gravação contém um formato e versão próprios, uma assinatura do mundo e uma assinatura das regras de movimento. Ao carregar, são verificados todos os campos antes de alterar o estado da partida.

- **Mapa alterado ou diferente:** rejeita o carregamento. A assinatura inclui toda a definição, mesmo nomes e outros dados visuais; é uma política conservadora. Alterar apenas a formatação ou a ordem das chaves JSON não muda a assinatura.
- **Movimento alterado:** rejeita. Remapear teclas não altera as regras de movimento e não invalida a gravação.
- **Versão desconhecida, JSON danificado ou campos inválidos:** rejeita. São também verificados cristais, interruptores, condições de ativação, checkpoints, fases de plataformas e estatísticas.
- **Gravação inexistente:** pede para guardar primeiro com F6.
- **Falha de escrita:** mantém o ficheiro anterior. A escrita usa um temporário na mesma pasta e substituição atómica depois de concluir a escrita.

Uma rejeição deixa o progresso em curso intacto e apresenta uma mensagem no jogo. F6 também **recusa sobrescrever uma gravação incompatível ou danificada**. Para começar outro registo, conserva o ficheiro antigo com outro nome ou escolhe um novo `--save-file`. Não há conversão automática nem eliminação de gravações antigas.

A verificação deteta incompatibilidades e dados inválidos; não é um sistema anti-cheat nem prova que todo o progresso foi obtido através de uma rota jogável. O limite de ficheiro é 2 MiB.

## Testar no Atelier

No teste F5 do perfil Salas, **F6/F9 usam apenas memória**, e a mensagem identifica «Só neste teste». Não leem nem escrevem os ficheiros das partidas normais.

Sair do teste com F5/Escape descarta essa gravação temporária. Voltar a testar cria outra sessão vazia. O documento do editor e o seu histórico não são modificados. **Ctrl+S** continua a guardar o mapa/mundo, não o progresso do teste.

## API reutilizável

`platform2d.gameplay.progress` contém:

- `capture_progress(world, movement, stats)`: constrói e valida um registo independente.
- `validate_progress(payload, world, movement)`: valida e devolve uma cópia, sem alterar o mundo.
- `restore_progress(payload, world, movement)`: valida integralmente, aplica o estado e devolve as estatísticas para a cena.
- `ProgressSlot(path)`: gravação em disco; sem caminho, funciona em memória.

`stats` contém `deaths`, `elapsed` e `won`. `movement` deve conter todos os parâmetros efetivos do controlador; o exemplo usa `vars(Movement(...))`. `RoomsScene(..., progress_slot=...)` recebe o destino, mantendo a decisão de armazenamento no anfitrião. Por predefinição usa memória, o que isola os testes do editor.

`RoomWorld` conserva uma cópia da definição para a assinatura e outra para os objetos em execução. Coleções, mecanismos e plataformas pertencem ao estado de sessão. Os carregamentos não restauram velocidades da personagem, callbacks de transição, subscrições de eventos, input ou estado de interface. As fases das plataformas são restauradas com interpolação sincronizada para evitar um salto visual.

O formato atual é `platform2d.rooms.progress`, versão 1. Ficheiros JSON usam campos explícitos e não executam código. Campos extra, chaves repetidas, números não finitos e referências desconhecidas são rejeitados.

## Verificar

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe tools\check_progress_workflow.py
```

O fluxo completo usa input para ativar mecanismos, recolher um cristal e chegar ao checkpoint. Guarda em disco e inicia **outro processo Python** que carrega, retoma e conclui o jogo sem mortes. Verifica ainda a gravação da vitória, F2/F9 e a rejeição de um mundo alterado. Todos os ficheiros de progresso deste teste usam uma pasta temporária; as imagens ficam em `artifacts/progress-saved.png`, `progress-loaded.png`, `progress-completed.png` e `progress-incompatible.png`.
