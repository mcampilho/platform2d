# Novos Horizontes — fase 0.22

A campanha principal passa a ter **12 níveis**: os oito anteriores, sem alterações nos mapas, seguidos de quatro novas aventuras. Cada aventura também pode ser jogada e editada separadamente.

| Abrir | Conteúdo |
| --- | --- |
| `Jogar-Campanha.cmd` | Os 12 níveis, pela ordem da campanha |
| `Jogar-Novos-Horizontes.cmd` | Apenas os quatro novos níveis |
| `Jogar-Campanha-8-Niveis.cmd` | A campanha anterior, incluindo as suas gravações |
| `Jogar-Fabrica.cmd` / `Editor-Fabrica.cmd` | Caixas e placas de peso |
| `Jogar-Subaquatico.cmd` / `Editor-Subaquatico.cmd` | Natação, correntes e oxigénio |
| `Jogar-Fuga.cmd` / `Editor-Fuga.cmd` | Câmara em avanço e ameaça de perseguição |
| `Jogar-Exploracao.cmd` / `Editor-Exploracao.cmd` | Capacidade adquirida e regresso ao átrio |

Os atalhos de edição abrem modelos sem substituir os mapas da campanha. **Editor-Campanhas.cmd** passa a abrir uma cópia da sequência de 12 níveis. Os novos tipos de objeto aparecem na barra de ferramentas quando o respetivo movimento está selecionado em **Missão / ambiente**.

## 9. Fábrica de Carga

Empurra as duas caixas com esquerda/direita. Cada caixa pesa 2 t; o jogador pesa 1 t. Uma placa mede o peso dos corpos apoiados sobre ela, pelo centro horizontal e pela altura dos pés. As duas placas precisam de permanecer carregadas para abrir a porta. Para concluir este puzzle, as caixas têm de manter todas as placas ativas, além de recolheres os cristais.

A primeira caixa também serve de degrau: sobe para ela e salta para a plataforma do cristal. Depois coloca a segunda caixa na outra placa e atravessa a porta. As caixas movem-se mais devagar do que a personagem; aproximar duas caixas não permite empurrá-las em cadeia.

**R repõe as caixas e regressa ao ponto de reaparecimento**, conservando os cristais já recolhidos. Uma caixa que caia para fora do mapa repõe automaticamente o puzzle. F6 guarda as posições das caixas; F9 recupera-as com a personagem no ponto de reaparecimento. Se uma caixa ocupar esse ponto, o carregamento procura uma posição próxima, livre e apoiada.

No editor, as caixas têm 48×48 unidades. Ajusta o peso mínimo nas propriedades de uma placa; coloca a sua base à altura do chão. Todas as portas de carga dependem de todas as placas do mapa. Uma porta que encontre um corpo na passagem espera antes de fechar, evitando sobreposições.

## 10. Torre Inundada

Nada com esquerda/direita. Mantém **Saltar ou Cima/W** para subir e **Baixo/S** para mergulhar. A água tem uma corrente horizontal suave. Fora dela, regressa a física normal de plataformas.

O oxigénio dura 12 segundos quando a cabeça está submersa. As bolsas assinaladas **AR**, ou sair da água, recuperam-no gradualmente. Os cristais orientam o percurso em ziguezague até à saída superior. Ficar sem oxigénio provoca o reaparecimento; o depósito volta cheio, tal como a vida se recupera nos outros níveis.

No editor, redimensiona volumes de água e bolsas de ar. A propriedade **Corrente** aceita valores de -80 a 80: negativos puxam para a esquerda. As bolsas renovam o ar, mas conservam o movimento de natação dentro do reservatório.

## 11. Fuga da Estação

A ameaça avança da esquerda a 65 unidades por segundo. A câmara avança mesmo se o jogador esperar e permite antecipar o cenário quando corre mais depressa. A faixa vermelha aparece quando a frente da ameaça está dentro da imagem; o contador indica a distância aproximada.

Ultrapassa blocos e fossos até à saída. Os checkpoints permitem retomar com a ameaça novamente atrás da personagem. A ameaça continua a avançar mesmo quando a câmara chega ao limite direito do mapa. R ou carregar uma gravação retoma a partir do checkpoint, reiniciando a perseguição nesse local.

## 12. Laboratório Esquecido

O átrio está à esquerda, inicialmente selado. Explora para a direita, encontra o cristal e o módulo **2x**, e regressa. O módulo desbloqueia a porta e permite um segundo salto no ar: salta, solta a tecla e prime-a novamente antes de aterrar.

A plataforma da saída exige usar a nova capacidade. A capacidade e o cristal mantêm-se após morte, R e carregamento; Nova campanha/F2 limpa-os. Este nível demonstra exploração com regresso numa área contínua. Não inclui ainda um mapa de mundo, várias capacidades ou viagens entre áreas independentes.

## Gravações e compatibilidade

Cada manifesto de campanha mantém a sua gravação separada. A sequência de 12 níveis não importa automaticamente o progresso da de oito: usa **Jogar-Campanha-8-Niveis.cmd** para continuar a partida anterior ou **Jogar-Novos-Horizontes.cmd** para experimentar já a expansão. Os controlos existentes são conservados; a ação Cima é acrescentada quando necessário.

## Validação e limites

O editor verifica tipos, dimensões, pesos, correntes, objetos essenciais, sobreposições iniciais de caixas e limites do mapa. **F8 devolve inconclusivo nestes quatro modos**: o pesquisador ainda não modela caixas, oxigénio, perseguição ou capacidades adquiridas. F5 permite testá-los nas regras reais. Não encontrar uma prova automática não significa que o mapa é impossível.

`tools/check_expansion.py` completa os quatro mapas fornecidos através de comandos reais, sem teletransportar a personagem, e verifica a recuperação das vitórias gravadas. É uma verificação destes mapas e destes percursos, não um solver geral para puzzles novos.

Os próximos passos da sequência original continuam a ser criar um pequeno jogo independente com o motor e preparar a distribuição. Os quatro estilos sugeridos ficam cobertos por esta expansão.
