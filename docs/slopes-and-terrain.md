# Rampas e superfícies inclinadas — versão 0.11.0

Esta fase acrescenta rampas de **45° nos dois sentidos**, reutilizáveis nos perfis Clássico, Precisão e Salas. A personagem sobe e desce sem precisar de saltar e pode saltar a partir da inclinação. O dash horizontal e as patrulhas também reconhecem estas superfícies.

## Experimentar Colinas

Abre **Jogar-Rampas.cmd**. O percurso usa as regras do Clássico: sete cristais, dois checkpoints e uma saída. Atravessa duas colinas e salta o fosso depois da primeira. Os comandos, o áudio e as preferências são os mesmos de Estação Aurora; **F3** mostra as teclas em vigor. Por predefinição, setas/A/D movem, Espaço salta e R regressa ao checkpoint.

**Editor-Rampas.cmd** abre uma cópia de Colinas no perfil Clássico. O documento só é guardado quando escolhes Guardar; o destino sugerido é `levels/minhas-colinas.json`.

```powershell
.venv\Scripts\python.exe -m examples.slopes
.venv\Scripts\python.exe -m examples.editor --profile slopes
```

`slopes` é um modelo inicial, não um quarto perfil do editor. Podes usar as rampas nos outros perfis e continuar a testar com F5.

## Desenhar rampas

| Ferramenta | Resultado, visto da esquerda para a direita |
|---|---|
| **U — Rampa /** | Sobe |
| **B — Rampa \** | Desce |

Escolhe uma ferramenta e pinta com o rato. O botão direito apaga; desfazer/refazer funciona por traço, como nos restantes tiles. A linha dourada identifica a superfície de apoio. Para criar uma subida longa, coloca cada tile seguinte **uma coluna à direita e uma linha acima**. Numa descida, coloca-o uma coluna à direita e uma linha abaixo. Os extremos devem encontrar chão plano ou outra rampa à mesma altura.

As rampas são **atravessáveis por baixo**, como as plataformas finas. Não têm paredes laterais ou teto sólido. Baixo + Salto permite largá-las, desde que exista espaço livre por baixo. Na demonstração há blocos sólidos sob as colinas: esses blocos continuam a impedir a passagem. A área triangular desenhada serve para representar a inclinação; a linha dourada é o contacto físico.

O corpo mantém-se retangular e vertical. Apoia-se no ponto mais alto da rampa sob os pés, pelo que um canto pode ficar suspenso sobre a inclinação. A personagem não roda, não escorrega sozinha e mantém a velocidade horizontal configurada. Deixa altura livre para todo o corpo; um teto baixo impede a subida sem empurrar a personagem para dentro do sólido.

Coloca saídas, entradas e checkpoints preferencialmente em pequenos patamares. Também podes ajustar a altura de um ponto sobre a rampa pelo inspetor; o aviso de «sem apoio imediato» usa a altura real da inclinação. A diagonal não constitui uma parede para wall jump.

## Mapas e compatibilidade

O formato JSON mantém `version: 1` e acrescenta dois símbolos à grelha: `/` e `\`. No texto JSON, uma barra invertida escreve-se `\\`; o editor trata essa codificação ao guardar.

```json
{"tiles": ["..../##\\....", ".../####\\...", "###......###"]}
```

Este excerto ilustra apenas a grelha; um mapa completo continua a precisar dos restantes campos e de um spawn. Os mapas antigos permanecem válidos. Versões do motor anteriores a 0.11 rejeitam os novos símbolos: usa esta versão para abrir níveis com rampas.

## Validação e soluções

A validação estrutural reconhece a altura de apoio inclinada e não trata o retângulo envolvente da rampa como um bloco sólido. A pesquisa de soluções do Clássico usa a mesma física do jogo e só confirma uma rota depois de a reproduzir exatamente.

A estimativa rápida que provava certos objetivos impossíveis em mapas planos fica desativada em mapas com rampas: essa estimativa não modelava subir a pé por uma diagonal. Se a pesquisa limitada não encontrar uma solução, o resultado será **inconclusivo**, nunca uma falsa prova de impossibilidade baseada nessa estimativa. Erros estruturais continuam a ser detetados. Em Precisão e Salas, confirma o percurso em F5, como nas versões anteriores.

## Implementação e testes

`Collider.slope` vale `0` para superfícies anteriores, `-1` para subida à direita e `1` para descida à direita. Uma rampa requer uma caixa quadrada e `one_way=True`. `surface(x, width)` calcula o apoio sob o corpo. Sem rampas, `move` conserva o algoritmo anterior; com rampas, divide deslocações em passos de até quatro unidades e trata as juntas e a aproximação aos tetos. A interpolação mantém a posição inicial do passo completo.

O teste `tools/check_slopes_route.py` guarda e reabre o mapa, usa as ferramentas U/B, verifica desfazer/refazer e completa Colinas através do teclado no teste do editor. Confirma sete cristais, subida, descida, salto do fosso, ausência de mortes e preservação do documento. Os testes de física incluem travessia nos dois sentidos, quedas rápidas, salto por baixo, salto a partir da rampa, descida voluntária, dash, teto baixo, plataformas móveis, patrulhas e reprodução de uma solução.

Ficam para outras fases: rampas com laterais sólidas, inclinações diferentes de 45°, tetos inclinados, curvas, looping, rotação da personagem e aceleração/deslizamento pela inclinação. As plataformas móveis continuam horizontais.
