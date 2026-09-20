# Fase 15 — guardar campanhas, menus e apresentação

Esta entrega reúne os três pontos: **gravação de campanhas**, **menus** e **feedback visual**. Abre **Jogar-Campanha.cmd**. A campanha começa agora no ecrã inicial, com Nova campanha, Continuar gravação, Opções e Sair.

## Menus e comandos

Usa **↑/↓ e Enter**, ou o rato, para escolher nos menus. **Esc** abre a pausa durante a partida e volta ao jogo quando estás no menu de pausa. **P** também abre/fecha a pausa; este comando pode ser alterado em F3. Perder o foco da janela pausa a campanha e exige retoma manual.

| Comando | Efeito |
|---|---|
| F6 | Guardar o progresso atual |
| F9 | Pedir para carregar a gravação |
| F2 | Pedir para reiniciar toda a campanha |
| R | Reaparecer no checkpoint do nível atual |
| Enter após vitória | Avançar ao nível seguinte |
| F3 | Configurar e guardar comandos |
| N durante a pausa | Avançar um único passo para diagnóstico |

Reiniciar uma partida em curso ou carregar por cima dela pede confirmação. O menu de saída oferece **Guardar e sair**, **Sair sem guardar** e **Cancelar**. Se a gravação falhar, Guardar e sair mantém o jogo aberto e apresenta o erro. Fechar a janela pelo X sai diretamente; não acrescenta uma gravação ao último ponto guardado.

O jogo continua a aceitar gamepad: Start para pausa, RB para próximo nível e LB para guardar por predefinição. O carregamento não recebe automaticamente RB porque esse botão já pertence ao avanço; podes atribuir outro em F3. Os menus e o painel de comandos usam teclado/rato.

## O que fica guardado

A gravação conserva:

- Nível atual, checkpoint e conclusão dos níveis anteriores.
- Melhorias e kits restantes.
- Caixas já recolhidas e alvos destruídos no nível atual.
- Disparos, mortes e tempo de jogo do nível e totais dos níveis concluídos.
- Vitória do nível, incluindo o resumo final da campanha.

Ao continuar, reapareces **no checkpoint, com vida completa**. Inimigos sobreviventes recuperam a resistência e os projéteis antigos desaparecem. A posição exata, o salto em curso, a invulnerabilidade temporária e as partículas não são gravados. Carregar um nível já vencido volta ao respetivo resumo, sem voltar a somar os totais.

Há gravação automática ao iniciar uma nova campanha, ativar um checkpoint, vencer um nível e entrar no seguinte. Entre estes momentos, usa F6 ou Guardar progresso no menu de pausa para conservar as recolhas e os combates mais recentes. R e a morte continuam a conservar o progresso da sessão, mas não criam por si uma gravação em disco.

O jogo usa **um ficheiro por caminho de campanha**, em `saves/campaign-<identificador>.progress.json`. O identificador é calculado a partir do caminho do manifesto, evitando misturar campanhas diferentes. Mover a pasta da campanha muda esse caminho; podes indicar explicitamente a gravação antiga:

```powershell
.\Jogar-Campanha.cmd --campaign "levels\minha-campanha\campaign.json" --save "saves\minha-partida.json"
```

## Compatibilidade e proteção dos ficheiros

O progresso tem formato e versão próprios. A identidade inclui os mapas, a ordem dos níveis, as regras de movimento e o catálogo de itens. Alterar estes dados invalida uma gravação anterior; alterar os comandos em F3 não a invalida.

Antes de carregar, todo o conteúdo é validado. Quantidades fora dos limites, IDs desconhecidos, vitória sem alvos destruídos, números inválidos e ficheiros demasiado grandes são rejeitados sem modificar a partida em curso.

A escrita usa um ficheiro temporário e substituição atómica. Uma gravação inválida, incompatível ou um ficheiro de outro tipo **não é sobrescrito**, nem por Nova campanha. A mensagem explica a falha; conserva o ficheiro original e usa outro caminho com `--save`, ou renomeia-o. Não existe migração automática entre mapas alterados nem histórico de várias gravações.

## Opções e apresentação

Opções permite ajustar o volume, ligar/desligar o som, configurar comandos e reduzir efeitos visuais. F10/F11/F12 continuam disponíveis. Volume, silêncio e efeitos aplicam-se à sessão; os comandos continuam a ter o seu próprio botão Guardar e persistem por perfil.

As melhorias visuais desta fase incluem:

- Fundo animado nos menus.
- Entrada suave ao começar, retomar, mudar de nível ou reaparecer.
- Partículas ao recolher objetos, destruir alvos e ativar checkpoints.
- Breve tonalidade de dano e celebração da vitória.
- Mensagens de gravação e carregamento separadas do cenário de combate.

**Efeitos visuais: reduzidos** desativa o fundo animado, as partículas, a tonalidade de dano e as transições. A física, o dano, os tempos da arma e os resultados da partida mantêm-se. As animações de movimento da personagem e os projéteis existentes continuam visíveis. As partículas têm limite fixo e não entram na gravação.

## Experimentar a entrega

1. Inicia uma nova campanha e recolhe uma melhoria.
2. Atinge o checkpoint, usa F6 e sai por Guardar e sair.
3. Volta a abrir Jogar-Campanha.cmd e escolhe Continuar gravação.
4. Confirma o inventário, os alvos destruídos e a vida reposta no checkpoint.
5. Experimenta pausa, opções, efeitos reduzidos e o avanço entre níveis.

O editor mantém o teste isolado de cada mapa. Estes menus, a gravação de campanha e os efeitos adicionais pertencem ao exemplo Campanha; os jogos anteriores mantêm a sua apresentação e os seus comandos.

Verificação automática:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe tools\check_campaign_experience.py
```

O percurso testa menus, opções, painel de comandos, pausa e gravação; lança outro processo de Python para continuar a partida e termina os três níveis sem mortes. Os ficheiros temporários de teste não substituem as tuas gravações.
