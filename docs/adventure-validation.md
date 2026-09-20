# Fase 20 — verificar percursos de Aventura

No **Editor-Aventura.cmd**, prime **F8**. Além de verificar a estrutura do mapa, o Atelier procura agora uma rota completa para os modos **Jetpack**, **Plataformas** e **Agarrar bordas**, desde que não existam alvos, torretas ou guardiões.

Para experimentar os mapas maiores, abre-os através do botão Abrir, ou a partir do Editor de Campanhas com **Editar mapa → F8**. A validação geral da campanha continua a verificar referências e estrutura; a pesquisa de percurso é feita dentro de cada mapa.

## Os três resultados

| Resultado | Significado | Ação sugerida |
|---|---|---|
| Solução confirmada | Uma sequência de comandos venceu nas regras reais do jogo, sem mortes. | Clica em **Ver solução** para a acompanhar. |
| Objetivo inacessível | Uma análise mais permissiva do que o movimento real já demonstra um bloqueio. | Usa **Ver** para localizar o objeto e revê o acesso. |
| Inconclusivo | A pesquisa limitada não conseguiu certificar uma rota, ou o mapa usa combate. | Testa manualmente com F5; não significa que o nível seja impossível. |

Uma rota confirmada precisa de cumprir todos os objetivos na mesma partida. Na oficina inclui recolher as peças na ordem correta, entregá-las, abastecer e descolar. No palácio inclui os cristais, as subidas pelas bordas e a saída. Uma peça isoladamente alcançável não basta para certificar a missão inteira.

## Acompanhar a solução

**Ver solução** abre o teste normal e reproduz os comandos encontrados. Podes observar o voo, as entregas, os saltos e as subidas. **F5 ou Esc** volta ao editor. A rota e o teste não alteram o mapa, o histórico ou as gravações da campanha.

O resultado é descartado quando alteras o mapa ou os parâmetros de movimento usados pela análise. Prime F8 novamente depois de mover uma plataforma, um objeto ou uma saída. **Esc** durante a pesquisa cancela-a e permite continuar a editar.

## O que é demonstrado como inacessível

Há duas verificações conservadoras antes da pesquisa:

- **Região fechada por sólidos.** Um modelo que ignora o tamanho da personagem, a gravidade, os perigos e as plataformas finas ainda não encontra acesso à região do objeto. Usa ligações diagonais e uma margem exterior generosa para evitar rejeitar passagens apenas por aproximação. Esta prova é desativada com checkpoints, tiles menores que 32 ou grelhas muito grandes.
- **Alcance vertical/deslocação.** Nos modos de plataformas e bordas, um limite generoso de movimento pode excluir certos objetivos. Para bordas, a análise acrescenta 64 unidades de altura ao salto e admite deslocação horizontal extremamente generosa. Se ainda assim o objetivo está fora do alcance, o movimento normal também não chega lá. Mapas com rampas não usam esta prova.

Estes diagnósticos não cobrem todos os obstáculos possíveis. Por exemplo, uma passagem demasiado estreita ou uma sequência delicada de saltos pode ficar inconclusiva em vez de receber uma declaração de impossibilidade. Um objetivo de saída adicional no modo Jetpack não é tratado como obrigatório: nesse modo, a saída efetiva é a descolagem.

## Limites e interpretação

A procura mantém até cerca de **18 000 estados** e usa um orçamento de **12 segundos de cálculo**, sem contar o tempo parado à espera de desenhar a interface. A análise geométrica inicial e a criação da cena também têm custo. Em mapas habituais a resposta pode chegar muito antes; isto não é uma garantia de tempo total para qualquer mapa.

A procura agrupa comandos e aproxima estados semelhantes. Por isso pode perder uma solução muito precisa. Em contrapartida, uma rota candidata é sempre repetida numa cena real antes de aparecer como confirmada. Se essa repetição falhar ou houver uma morte, o resultado é inconclusivo.

Não procura a rota mais curta nem avalia diversão ou dificuldade. Não certifica combate, plataformas móveis, portas entre salas ou todas as combinações futuras de mecânicas. Os diagnósticos da pesquisa não impedem guardar um mapa estruturalmente válido nem testar manualmente uma ideia.

## Verificação da entrega

`tools/check_adventure_validation.py` aciona F8 no Atelier para a oficina, o vale e o palácio, reproduz cada solução e verifica vitória sem mortes e preservação dos ficheiros. `tests/test_adventure_reachability.py` testa também peças fechadas, altura excessiva, limites de pesquisa, cancelamento, alteração de movimento e rejeição de candidatos que falhem na cena real.
