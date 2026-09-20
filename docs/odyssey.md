# Odisseia Aurora — voo, foguetão, scroll e bordas

Abre **Jogar-Odisseia.cmd** e escolhe **Nova campanha**. A versão 0.17 acrescenta uma aventura de **sete etapas**, inspirada nas ideias de montagem e abastecimento de Jetpac e na subida de bordas de Prince of Persia. Usa os gráficos e sistemas próprios deste projeto.

| Ordem | Nível | Novidade |
|---|---|---|
| 1 | Oficina Orbital | Voar, transportar peças, montar e abastecer o foguetão. |
| 2–5 | As quatro salas da Expedição Aurora | Bastião, Jardins, Conduta e Laboratório, no mesmo estado e ordem anteriores. |
| 6 | Vale das Três Luas | Percurso de 2400 unidades, scroll lateral, três planos de fundo e zonas perigosas. |
| 7 | Palácio das Falésias | Torre de 1152 unidades de altura, scroll vertical e oito bordas para agarrar e subir. |

## Oficina Orbital

Mantém **Espaço/Z** para ativar o jetpack; larga para descer. Usa esquerda/direita para orientar o voo. **Baixo** permite atravessar plataformas suspensas durante a descida.

1. Recolhe as peças na ordem **1 Motor → 2 Depósito → 3 Cockpit**. Cada uma tem uma forma diferente e a próxima está assinalada. Só podes levar uma carga de cada vez; as peças posteriores aguardam a sua vez.
2. Regressa ao foguetão e prime **E** para a instalar.
3. Repete até montar as **três peças**.
4. Recolhe as caixas **F**, uma de cada vez, e entrega os **três depósitos de combustível** com E.
5. Sem carga e junto do foguetão completo, prime **E novamente** para embarcar e descolar.

O combustível só pode ser recolhido depois de concluir a montagem. A imagem do foguetão muda à medida que instalas as peças. Cada entrega de combustível pinta mais um terço da nave de âmbar, desde a base; o contador também permanece visível. A descolagem anima a subida da nave e apresenta a viagem para o planeta Aurora; Enter no resumo abre o Bastião de Entrada.

No gamepad, A ativa o jetpack e B interage por predefinição. Os comandos podem ser alterados em F3. Preferências existentes são preservadas; se B já estiver ocupado, escolhe um botão livre para Interagir. O painel e os menus continuam a usar teclado/rato.

## Scroll e parallax

O vale acompanha a personagem horizontalmente; o palácio acompanha-a verticalmente. As posições dos objetos continuam a ser coordenadas do mapa, independentemente da câmara. Os limites impedem mostrar áreas exteriores ao nível.

Os fundos têm três planos: estrelas e luas ao longe, relevo/arquitetura intermédios e formas mais próximas. Movem-se a 12%, 30% e 60% da deslocação da câmara, criando profundidade. O cenário jogável move-se à velocidade total. Os fundos são decorativos e não têm colisão. A opção de efeitos reduzidos imobiliza o parallax, mantendo o movimento da câmara.

Os quatro níveis anteriores continuam com o seu ecrã fixo. Não precisaram de ser redimensionados nem convertidos para a nova física.

## Agarrar bordas no palácio

Salta na direção da face de uma plataforma sólida. Quando a personagem começa a descer e as mãos chegam perto da borda, agarra-a automaticamente.

- **Espaço/Z ou E:** subir, depois de largar e voltar a premir a tecla.
- **Baixo:** largar a borda.
- **R:** regressar ao checkpoint, como nos outros níveis.

A subida dura um breve movimento em duas partes: primeiro elevar o corpo, depois colocá-lo sobre a plataforma. A deteção verifica espaço para o corpo e para o percurso; não permite atravessar um teto baixo. Plataformas atravessáveis por baixo, rampas e plataformas móveis não são bordas agarráveis nesta entrega.

As subidas do palácio têm 96 unidades, acima do alcance vertical do salto normal. As mãos conseguem atingir a borda e completar a subida. Há checkpoints intermédios; cair de uma plataforma não implica necessariamente morrer, mas pode obrigar a voltar a subir.

## Gravar e retomar

F6/F9, os menus e os checkpoints mantêm-se. Na oficina, **cada entrega** também guarda automaticamente. A gravação inclui peças instaladas, combustível entregue e eventual carga transportada. Carregar ou reaparecer não duplica a carga nem repõe as peças já entregues.

Se guardares durante a descolagem, antes do resumo, a retoma regressa ao checkpoint com o foguetão pronto; podes embarcar novamente. Uma vitória já gravada retoma o resumo. Nos níveis com scroll, a retoma reposiciona imediatamente a câmara junto do checkpoint. Estar agarrado a uma borda ou a meio de uma subida é estado temporário e não é retomado literalmente.

As campanhas anteriores mantêm os seus manifestos e gravações:

- **Jogar-Expedicao.cmd:** as quatro salas da versão 0.16.
- **Jogar-Campanha-Classica.cmd:** a campanha original de três arenas.

A Odisseia usa uma gravação própria. A versão 0.18 conserva as peças já instaladas nas gravações antigas, mesmo fora de ordem. Se transportavas uma peça posterior à próxima necessária, essa peça regressa ao seu lugar original no mapa, para não bloquear a montagem. Não converte nem substitui as anteriores.

## Editar aventuras

**Editor-Aventura.cmd** abre uma cópia da Oficina Orbital. O perfil **Aventura** acrescenta:

- **9:** peça; **0:** combustível; **O:** foguetão.
- **Missão / ambiente… → Movimento:** plataformas, jetpack ou agarrar bordas.
- **Missão / ambiente… → Câmara:** ecrã fixo, horizontal, vertical ou dois eixos.
- **Tamanho:** mapas entre 960×576 e 3840×2048 unidades, respeitando a grelha de tiles.

A ordem das peças é a sua ordem de criação na lista `objects` do JSON; mover uma peça no mapa não muda essa ordem.

A oficina usa ecrã fixo, um foguetão e pelo menos uma peça e um combustível; o desenho suporta até três peças e nove depósitos. Os objetos jogáveis devem ficar abaixo do painel, com Y mínimo 264. Define as peças e o foguetão antes de mudar um mapa vazio para modo jetpack. Durante a construção, F8 pode indicar os elementos ainda em falta.

Scroll horizontal mantém altura 576; scroll vertical mantém largura 960. Para ampliar os dois eixos, escolhe Dois eixos. Os perfis anteriores mantêm os seus limites.

Para estudar diretamente os mapas maiores:

```powershell
.\Editor.cmd --map "examples\campaign\assets\odyssey-valley.json"
.\Editor.cmd --map "examples\campaign\assets\odyssey-palace.json"
```

Usa Guardar como para criar variantes. F5 testa o movimento e a câmara do perfil Aventura. Desde a fase 20, F8 procura uma rota completa e disponibiliza Ver solução quando a confirma nas regras reais. Consulta [a validação de Aventura](adventure-validation.md).

## Verificação

`tools/check_odyssey.py` recolhe e entrega as seis cargas, testa a retoma entre entregas, descola, atravessa o vale e sobe as oito bordas do palácio sem mortes. As quatro salas intermédias continuam cobertas pelo percurso `tools/check_varied_campaign.py`.

Os testes isolados verificam carga única, abastecimento após montagem, gravações inválidas, voo, subida, largar bordas, tetos bloqueados, câmaras, limites de mapas e a preservação dos quatro mapas existentes.


A fase **0.21** acrescenta [poses e efeitos para as ações](action-presentation.md), mantendo os comandos e as regras descritos neste guia.
