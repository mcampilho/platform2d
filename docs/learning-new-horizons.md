# Aprender com quatro estilos — fase 0.22

Esta fase mostra como acrescentar regras diferentes sem copiar o ciclo completo de jogo. Os quatro níveis usam `ExpansionScene`, uma especialização de `AdventureScene`, que já fornecia câmara, plataformas, recolhas, checkpoints e apresentação.

## 1. Acrescentar geometria antes do movimento

`RangedScene.update` chama agora `prepare_world` antes de mover a personagem. A implementação original não faz nada. A expansão usa o ponto de extensão para atualizar caixas, calcular portas abertas e fornecer os colisores dinâmicos à física e aos projéteis.

Em `platform2d/gameplay/cargo.py`, cada caixa é um `Body` normal. A gravidade e os obstáculos usam o mesmo `move` da personagem. O sistema apenas decide quando aplicar velocidade horizontal: jogador apoiado, junto à face da caixa e a empurrar na direção correta. As restantes caixas continuam sólidas, pelo que não há empurrão em cadeia.

As placas consultam a posição e o peso dos corpos, sem desenhar nada. A cena transforma esse resultado em portas abertas e condições de vitória. A geometria original do mapa é reposta ao terminar cada atualização, incluindo quando ocorre uma exceção.

Experiência: muda o peso de uma placa para 1 no editor e observa o jogador ativá-la. A saída da Fábrica continua a exigir caixas nas placas: as condições de abrir uma porta e de concluir uma missão podem ser diferentes.

## 2. Trocar o controlador, conservar as colisões

`platform2d/actors/exploration.py` contém dois controladores opcionais:

- `SwimController` recebe um sensor de água e a corrente local. Substitui as velocidades pretendidas enquanto está submerso, mas deixa o movimento e as colisões a cargo de `Character`.
- `ExploreController` permite um salto adicional quando a capacidade está ativa. O sinal de tecla premida evita saltos repetidos por manter a tecla; aterrar devolve o salto adicional.

O oxigénio pertence à cena, porque é uma regra da missão. A cabeça dentro de água consome-o; uma bolsa de ar recupera-o. Separar o sensor de movimento do sensor de respiração permite ter a cabeça fora de água e os pés ainda submersos.

Experiência: altera a corrente da Torre no editor, testa o efeito e desfaz. Depois compara com alterar a gravidade: a corrente afeta a água, enquanto a gravidade afeta o movimento fora dela.

## 3. Separar a perseguição da câmara

Na Fuga, o tempo da perseguição avança apenas durante a simulação. A frente da ameaça determina se o jogador foi apanhado; a câmara decide o que mostrar. A câmara pode acompanhar quem corre à frente, e a ameaça continua mesmo quando a imagem já não pode avançar.

Pausar congela o tempo. Reaparecer reinicia a perseguição relativamente ao checkpoint. Esta separação evita que o jogador morra apenas por tocar numa margem visual ou que a ameaça pare ao chegar ao fim do scroll.

## 4. Conservar apenas o progresso adequado

A capacidade de salto duplo usa os IDs de objetos recolhidos, já existentes no contrato de gravação. O controlo consulta esse estado em cada passo; reiniciar o controlador não apaga a aquisição.

As caixas precisam de dados adicionais: a gravação guarda posições por ID, valida números finitos, limites e sobreposições antes de substituir a cena atual. Velocidades, oxigénio e relógio da perseguição não são preservados: o carregamento segue o contrato de regresso ao checkpoint, com recursos recuperados.

## 5. Verificar regras e percursos

Executa na pasta do projeto:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_expansion.py
.venv\Scripts\python.exe tools\check_expansion.py
```

Os testes cobrem bloqueio de caixas, peso, queda sobre a personagem, oxigénio, corrente, pausa, capacidade, reinícios, gravações inválidas e edição. A ferramenta joga os quatro mapas com sequências de ações e guarda imagens em `artifacts`.

`tools/build_expansion_levels.py` explica como foram construídos os mapas em dados. Executá-lo substitui os quatro mapas de demonstração da expansão e os seus manifestos; guarda experiências pessoais noutros ficheiros. A campanha antiga é apenas lida para construir a nova sequência.
