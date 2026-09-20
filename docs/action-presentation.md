# Apresentação das ações — fase 0.21

Abre **Jogar-Duelo.cmd** para ver as novas animações de espada, ou **Jogar-Campanha.cmd** e inicia uma campanha para experimentar o transporte na Oficina Orbital. Os comandos mantêm-se: **J** ataca, manter **L** defende e **E** entrega a carga.

O explorador levanta os braços quando transporta uma peça ou combustível. A carga acompanha a posição interpolada da personagem, evitando deslocamentos entre os dois desenhos. Motor, depósito e cockpit conservam as suas formas distintas e a ordem de montagem.

No duelo, explorador e Guardião têm corpos articulados: pernas em movimento, preparação com espada levantada, extensão do golpe, recuperação, defesa frontal e reação ao dano. O Guardião usa armadura, capa e uma crista no capacete. Os rótulos PREPARA, GOLPE, RECUPERA, DEFESA e VULNERÁVEL ajudam a identificar a oportunidade de contra-atacar.

Pequenas marcas locais distinguem desvio perfeito, bloqueio e dano. Duram 0,18 segundos de simulação e param durante a pausa. Um contacto ignorado pela invulnerabilidade não produz uma marca de dano. Em **Opções**, desativar os efeitos visuais remove estas marcas, os rastos da espada e a oscilação decorativa de repouso; as poses necessárias para compreender o combate continuam visíveis.

## Experimentar

1. Na Oficina, recolhe o motor e observa os braços e a carga enquanto voas. Entrega-o junto à nave com E.
2. No Duelo, aproxima-te do Guardião e observa a preparação antes do golpe.
3. Defende perto do momento do impacto e contra-ataca quando aparecer VULNERÁVEL.
4. Compara a apresentação com efeitos ligados e desligados nas Opções.

Esta fase altera a apresentação. Os tempos, alcance, resistência, dano, colisões e regras de gravação mantêm-se. Os exemplos anteriores conservam os seus sprites; não existe ainda um editor de animações nem novas regras de combate.

## Verificação

`tools/check_action_presentation.py` gera uma folha ampliada das poses e uma imagem da Oficina em `artifacts`. A folha demonstra o desenhador reutilizável; a pose de transporte do Guardião é apenas uma amostra, não um comportamento da sua inteligência artificial.

`tests/test_action_presentation.py` verifica as fases do ataque, prioridade do dano, independência do desenho, pausa, limpeza dos efeitos e preservação da missão ao desenhar cargas. `tools/check_duel.py` percorre o duelo com ações reais, incluindo desvios e contra-ataques. Os percursos de aventura continuam a ser verificados pelas ferramentas da fase anterior.
