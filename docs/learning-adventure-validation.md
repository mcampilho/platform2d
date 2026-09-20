# Aprender com a validação de Aventura

Esta fase separa duas afirmações: **encontrar um percurso** e **demonstrar que esse percurso funciona**. A primeira pode usar aproximações para pesquisar mais depressa; a segunda tem de usar as regras do jogo.

## 1. Um estado contém mais do que uma posição

`AdventureSearch`, em `platform2d/tools/adventure_reachability.py`, reutiliza a estrutura de pesquisa do Clássico. Cada nó guarda uma personagem, os cristais recolhidos, o checkpoint e os comandos anteriores. A versão Aventura acrescenta o estado do foguetão e distingue direção, borda agarrada, progresso da subida e intervalo até voltar a agarrar.

Dois jogadores na mesma posição não têm necessariamente as mesmas opções: um pode estar a subir, outro a cair; um pode transportar uma peça e outro ter as mãos vazias. O estado pesquisado tem de conservar essas diferenças.

## 2. Expandir comandos, não teletransportar

Cada ramo simula um pequeno grupo de atualizações a 60 Hz, com combinações de direção e salto. O Jetpack usa impulso e descida; numa borda surgem opções de subir, esperar ou largar. A personagem continua a usar `Character`, `JetpackController` ou `LedgeController` e as colisões existentes.

A missão do foguetão usa o próprio `RocketMission`. A pesquisa não inventa uma montagem alternativa nem ignora a carga transportada. O custo estimado favorece a próxima peça ou entrega; nos percursos a pé favorece os cristais e a saída. Essa estimativa ajuda a encontrar uma rota, mas não promete a mais curta.

## 3. Confirmar num segundo percurso

Quando um ramo parece vencer, reconstruímos os comandos através dos nós anteriores. Uma fábrica fornecida pelo anfitrião cria então a cena real, com uma cópia do mapa. A sequência inteira é executada novamente, incluindo o tempo de descolagem.

Só uma vitória sem mortes produz `solved` e disponibiliza os comandos para Ver solução. Sem fábrica de jogo, sem vitória ou com morte, o candidato permanece inconclusivo. Assim, uma divergência entre o modelo de pesquisa e as regras da cena não transforma automaticamente uma aproximação numa falsa solução.

## 4. Provar um bloqueio exige ser mais generoso

A ausência de rota na pesquisa não prova impossibilidade. Para obter alguns resultados negativos seguros, usamos modelos deliberadamente mais permissivos.

A análise de regiões fechadas trata a personagem como um ponto, ignora perigos e aceita diagonais. A análise vertical de bordas admite mais altura do que o alinhamento das mãos e a subida oferecem, além de deslocação horizontal muito maior. Um bloqueio que persiste nessas condições também bloqueia o movimento normal abrangido pelo modelo.

Quando não conseguimos justificar essas condições — por exemplo, numa combinação ainda não modelada — saltamos essa prova. Isto reduz o número de diagnósticos negativos, mas evita afirmar mais do que sabemos.

## 5. Orçamento, cancelamento e resultados antigos

O editor chama pequenos passos de pesquisa entre desenhos da interface. A repetição da rota também é repartida em grupos de atualizações. Um limite de estados e um orçamento de cálculo impedem que a procura cresça indefinidamente.

O resultado fica associado à cópia do mapa e aos parâmetros de movimento. Alterar qualquer um invalida-o. Escape descarta a pesquisa pendente. O mapa e as gravações de progresso não fazem parte do estado temporário da análise.

## Exercício

Abre o palácio e confirma a solução com F8. Move um cristal para uma altura muito superior, sem acrescentar apoios, e repete. Depois devolve-o a uma posição alcançável e observa a solução reproduzida. Por fim, cria uma passagem estreita: se o resultado for inconclusivo, compara o que a pesquisa conseguiu demonstrar com o que tu consegues jogar manualmente.
