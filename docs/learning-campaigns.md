# Aprender com a fase 14: ligar jogos sem copiar as suas regras

Nesta entrega, seguimos a viagem de uma melhoria entre dois mapas. Joga o primeiro nível de Operação Aurora, recolhe a caixa de Potência e termina-o. No segundo nível tens outra posição inicial, novos alvos e vida completa, mas conservas o dano adicional.

## 1. A sequência é um sistema pequeno

Em [campaign.py](../platform2d/gameplay/campaign.py), `CampaignProgress` conhece apenas IDs e ordem. `complete()` assinala o nível atual; `advance()` só permite avançar depois de o concluir. O último nível pode estar concluído sem existir outro para abrir.

Esta distinção permite mostrar um resumo entre níveis. Também impede contar a mesma vitória várias vezes: `complete()` devolve `False` se já foi registada. O sistema não conhece Pygame, mapas, armas ou personagens.

**Experiência:** num pequeno programa, cria `CampaignProgress(["a", "b"])` e chama `advance()` antes de `complete()`. O índice não muda. Depois completa, avança e observa `current`.

## 2. O ficheiro descreve a ordem

O manifesto `examples/campaign/assets/campaign.json` referencia três mapas normais. `load_campaign()` abre e valida todos antes da primeira partida. Assim, um erro no terceiro mapa aparece ao iniciar, em vez de surgir depois de já teres vencido dois níveis.

Os mapas são dados do exemplo; o núcleo do motor não precisa de saber que existem três arenas ou que se chamam Operação Aurora.

**Experiência:** copia o manifesto e os mapas para uma pasta própria e troca a ordem dos dois primeiros. A ordem muda sem alterar o código da cena ou do motor.

## 3. Uma cena coordena outra cena

Abre [scene.py](../examples/campaign/scene.py). `CampaignScene` tem uma `active`, que é uma `RangedScene` já existente. Enquanto o nível decorre, encaminha `update()` e `draw()` para essa cena. A física, os disparos, os kits e os inimigos continuam com as regras das fases anteriores.

Quando `active.won` passa a verdadeiro, a campanha regista as estatísticas uma única vez. Nos passos seguintes, congela a cena e espera pela ação `continue`. Uma nova cena só é criada quando o jogador pede para avançar.

Repara na construção da próxima cena antes da alteração do índice. Esta ordem evita deixar a campanha a apontar para um nível que falhou durante a criação.

## 4. Decidir o que viaja e o que fica

O inventário é passado à nova cena e a arma é recalculada com `upgraded_weapon`. A nova cena cria os seus próprios inimigos, checkpoints e conjunto de objetos recolhidos.

Isto separa dois tempos de vida:

| Estado | Dura até |
|---|---|
| Melhorias, kits e estatísticas totais | Reiniciar a campanha |
| Objetos recolhidos e alvos destruídos do mapa | Passar ao nível seguinte |
| Projéteis em voo | Morrer, reiniciar ou terminar o nível |

Na fase 14, não copiávamos o inventário para um ficheiro; a fase 15 acrescenta essa capacidade, explicada no [guia seguinte](learning-campaign-experience.md). As duas cenas referem o mesmo objeto de inventário durante a passagem; a cena anterior deixa depois de estar ativa. Esta escolha é simples porque não existe regresso a níveis anteriores. Um sistema de caminhos alternativos ou gravação precisaria de um contrato de estado mais abrangente.

**Experiência:** altera a arma base do segundo mapa numa cópia, usando o Atelier. Confirma que a melhoria se soma ao dano desse mapa, sem transportar a arma base do primeiro.

## 5. Reiniciar tem um âmbito explícito

R é encaminhado para a cena ativa e regressa ao checkpoint. F2 é tratado primeiro pela campanha: limpa a progressão e cria novamente o primeiro nível. Se F2 fosse simplesmente encaminhado, apenas o nível atual seria reiniciado e a campanha manteria os totais anteriores.

Esta é uma decisão de produto que aparece diretamente na ordem das condições de `update()`.

## 6. Testar a ligação entre sistemas

[test_campaign.py](../tests/test_campaign.py) verifica a sequência, o transporte de inventário, os IDs locais, os totais registados uma única vez e o reinício completo. [check_campaign_route.py](../tools/check_campaign_route.py) verifica o percurso real através de eventos de teclado.

Os testes isolados encontram erros de regras; o percurso encontra problemas de integração. A campanha consegue reutilizar os mesmos IDs de objetos em todos os mapas porque o teste confirma que o estado local é renovado a cada passagem.
