# Aprender com o editor de campanhas

Nesta fase a principal novidade é uma ferramenta de criação. Não precisamos de mudar a física, a IA ou as regras do foguetão para organizar os mesmos níveis de outra maneira.

## 1. Separar o documento da interface

`platform2d/tools/campaign_model.py` contém `CampaignDocument`. Guarda nome e etapas, oferece operações como `add`, `move`, `remove` e `rename_stage`, e mantém histórico por cópias do documento. Não depende de Pygame nem das cenas dos exemplos.

Cada alteração é atómica em memória: primeiro guarda uma cópia, aplica a operação e só regista histórico se houve uma alteração real. Uma operação inválida deixa o documento anterior intacto. A seleção da linha e a posição da lista pertencem à interface; não entram no ficheiro de campanha.

## 2. Caminhos internos e caminhos exportados

Ao carregar, os caminhos dos mapas são resolvidos em relação à pasta do manifesto e guardados como caminhos absolutos na sessão de edição. Isto evita que Guardar como mude involuntariamente o significado de uma referência.

Ao exportar, o editor calcula os caminhos relativos à nova pasta. O documento em memória mantém os mesmos destinos; o ficheiro usa referências adequadas à sua localização. A escrita passa por um ficheiro temporário na mesma pasta e termina numa substituição atómica. O estado marcado como guardado só muda depois de a escrita terminar.

O editor também recusa substituir um dos mapas referenciados pelo manifesto. Campanha e mapa são documentos diferentes, mesmo tendo ambos extensão JSON.

## 3. Reutilizar a validação

`inspect()` abre cada referência com `MapDocument`, aproveita as validações do mapa e acrescenta contexto: número e ID da etapa. O resultado inclui o documento carregado, nome, perfil e problemas encontrados.

Abrir uma campanha não exige que todas as referências estejam resolvidas: precisamos de conseguir corrigir um mapa em falta. Guardar e jogar exigem uma estrutura válida. Esta diferença entre edição e execução é importante em ferramentas de criação.

## 4. Testar através de uma fábrica

`platform2d/tools/campaign_editor.py` recebe a fábrica de teste através de `examples/editor/profiles.py`. O anfitrião fornece `CampaignScene`; o editor não importa diretamente as regras do exemplo.

O teste completo constrói uma campanha com todas as etapas. O teste a partir da seleção usa uma cópia do sufixo da lista. Assim não é preciso fingir que etapas anteriores foram vencidas, nem modificar o progresso ou o inventário de uma partida existente.

F5 testa a sequência e Enter exercita a transferência de inventário já implementada. Ao terminar, o objeto da sessão é descartado. Nenhuma gravação de jogador é necessária para testar uma criação.

## 5. Dois históricos independentes

Editar uma etapa abre um `LevelEditor` com o respetivo `MapDocument`. O mapa tem o seu próprio histórico e a sua própria decisão de guardar. F4 volta à campanha, que relê os ficheiros para atualizar os detalhes.

A campanha guarda referências; o mapa guarda geometria e objetos. Manter esta separação evita transformar uma pequena mudança de ordem numa reescrita de todos os níveis.

## Exercício

Cria uma campanha com o Pátio do Guardião primeiro e o Vale das Três Luas depois. Usa Começar aqui, testa a sequência e guarda-a com outro nome. Depois cria uma cópia de um dos mapas, muda o seu título no editor e usa Trocar mapa para a incluir. Compara os ficheiros guardados: o manifesto contém a sequência e o mapa contém o cenário.

Para acompanhar a verificação, lê `tests/test_campaign_editor.py` e `tools/check_campaign_editor.py`. O percurso integrado usa ações reais do jogador e confirma que o inventário transita entre duas etapas enquanto os ficheiros de origem permanecem intactos.
