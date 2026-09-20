# Aprender com a fase 17: capacidades, objetivos e câmara

Esta entrega acrescenta três sistemas diferentes sem substituir o movimento dos jogos anteriores. Começa por jogar a Oficina Orbital e depois acompanha esta ordem de leitura.

## 1. Uma missão pode ter várias fases

[rocket.py](../platform2d/gameplay/rocket.py) não conhece imagens nem posições. Guarda três coisas: IDs das peças entregues, IDs do combustível entregue e a carga transportada.

`take()` só aceita uma carga de cada vez. `deliver()` transfere essa carga para o conjunto apropriado e esvazia as mãos. `assembled` e `ready` são resultados calculados a partir dos conjuntos; não são indicadores independentes que possam ficar desatualizados.

**Experiência:** tenta recolher combustível antes de montar a nave. Depois monta-a e tenta outra vez. A posição da caixa não mudou; mudou a condição que autoriza a recolha.

Na cena, tocar na caixa pede a recolha e E junto do foguetão pede a entrega. Outra pressão de E, sem carga e com os objetivos concluídos, inicia a descolagem. Separar entrega de partida evita que a última entrega dispare uma viagem involuntária.

## 2. Capacidades diferentes, o mesmo corpo

[traversal.py](../platform2d/actors/traversal.py) acrescenta dois controladores:

- `JetpackController` aplica aceleração vertical enquanto a ação de salto está mantida. O corpo continua a usar as colisões existentes.
- `LedgeController` amplia o movimento normal com os estados de agarrar e subir. Os níveis anteriores continuam com `ArcadeController`.

O controlador de bordas recebe os colisores em `prepare()`. Depois da física, procura uma face sólida perto das mãos, durante a descida. Para não agarrar uma divisão interior da grelha, verifica se há espaço para o corpo suspenso e para ficar em pé no topo.

Ao subir, verifica duas regiões: o movimento vertical fora da parede e o movimento horizontal sobre o topo. Só depois inicia a animação de 0,3 s. A aparência não autoriza atravessar colisores.

**Experiência no editor:** baixa um teto sobre uma borda. A personagem não deve conseguir encaixar-se num espaço menor do que o seu corpo. Não testes apenas uma plataforma isolada: os vizinhos também importam.

## 3. Coordenadas do mundo e do ecrã

Em [adventure.py](../examples/campaign/adventure.py), os objetos continuam a ter posições no mundo. Para desenhar um objeto com scroll:

```text
ecrã_x = mundo_x - câmara_x
ecrã_y = mundo_y - câmara_y + altura_do_painel
```

O painel superior tem 96 unidades e fica fora da área deslocada. A câmara acompanha o corpo com suavização e guarda a posição anterior para interpolação, tal como a personagem. Ao reaparecer, usa `snap=True`: não mostra uma viagem da câmara desde o sítio onde morreste.

Os colisores e a gravação nunca recebem coordenadas do ecrã. Mover a câmara não pode mudar o local de uma parede ou de um checkpoint.

## 4. Parallax é uma transformação de desenho

[parallax.py](../platform2d/rendering/parallax.py) desenha três planos com fatores diferentes. O fator pequeno parece distante porque se desloca pouco; o cenário jogável desloca-se integralmente.

As formas são calculadas de maneira determinística. Não usam o gerador aleatório do jogo nem entram na física. O índice das formas repetidas é calculado a partir da posição global da câmara para não trocar o desenho ao passar de um segmento para outro.

**Experiência:** numa cópia do módulo, coloca os três fatores a 1. A profundidade desaparece porque tudo se move em conjunto. Repõe os valores antes dos testes.

## 5. Reutilizar a cena sem copiar o combate

`AdventureScene` reutiliza a recolha, vida, projéteis e checkpoints de `RangedScene`. O desenho foi separado em mundo, painel e sobreposição de pausa/vitória. A aventura pode deslocar só o mundo e manter o painel fixo.

[factory.py](../examples/campaign/factory.py) escolhe a cena pelo perfil do mapa. A campanha usa a mesma função ao iniciar, avançar e carregar uma gravação. Isso evita que um mapa de voo funcione ao entrar, mas volte com um controlador normal depois de carregar.

## 6. Persistir apenas o estado necessário

As peças e o combustível usam IDs, como os cristais. A gravação valida que nenhum objeto aparece simultaneamente entregue e transportado, e que não há combustível entregue antes de terminar a montagem.

Já a câmara, a chama do jetpack, a suspensão numa borda e o movimento de subida são temporários. A retoma reconstrói-os a partir do checkpoint. Durante uma descolagem ainda não concluída, a gravação conserva o foguetão pronto e permite repetir a partida.

Lê [test_odyssey.py](../tests/test_odyssey.py) para os casos isolados e [check_odyssey.py](../tools/check_odyssey.py) para os percursos completos. Os quatro mapas anteriores são comparados com os originais para confirmar que foram reutilizados sem alterações.
