# Laboratório ambiental: Mundo Vivo

Abre `Jogar-Ambiente.cmd` ou executa `python -m examples.environment` na raiz do projeto. O percurso apresenta quatro zonas, cada uma com uma regra do cenário. Os checkpoints permitem repetir a experiência a partir do último setor; R reaparece no checkpoint e F2 reinicia o percurso.

1. **Plataforma móvel:** salta para a plataforma verde. O motor transporta quem está apoiado nela e resolve as colisões durante o movimento.
2. **Interruptor:** aproxima-te do botão amarelo e prime E. A porta vermelha deixa de bloquear a passagem e fica aberta até reiniciares o percurso.
3. **Água:** dentro da zona azul, Espaço ou cima permite subir e baixo permite mergulhar. A corrente horizontal altera o movimento; fora de água regressa o controlo normal.
4. **Gravidade reduzida:** dentro da zona violeta, a gravidade diminui, prolongando o salto para atravessar o fosso. A gravidade continua a apontar para baixo e volta ao valor normal à saída.

As definições do movimento e dos comandos estão em `examples/environment/settings.json`. O mapa e as instruções visíveis no jogo estão em `examples/environment/assets/laboratory.json`. Para criar outra experiência, copia esses ficheiros e executa `python -m examples.environment --map outro-mapa.json --settings outras-definicoes.json`.

**F6** liga ou desliga partículas, brilhos e sombras durante o jogo. Também podes iniciar sem esses efeitos, definindo `"effects": {"enabled": false, "shadows": true}` no ficheiro de definições. Para manter partículas e brilhos sem sombras, usa `"enabled": true` e `"shadows": false`. As partículas assinalam a entrada na água, a aterragem, a ativação do interruptor e a entrada na zona de gravidade; os brilhos ajudam a identificar objetos e áreas especiais. Uma pequena luz acompanha o jogador e projeta sombras a partir dos blocos sólidos, da plataforma e da porta enquanto está fechada. Abrir a porta retira também a sombra correspondente. Os efeitos são visuais e não alteram colisões, movimento nem objetivos. O módulo de partículas `platform2d/rendering/feedback.py` aceita coordenadas do mundo com um deslocamento de câmara ao desenhar; `platform2d/rendering/lighting.py` fornece brilhos reutilizáveis e guarda as imagens radiais em cache. `platform2d/rendering/shadows.py` desenha as sombras dos retângulos próximos da luz.

A câmara antecipa suavemente a direção do movimento e recebe impulsos muito pequenos em acontecimentos ambientais. Define `effects.camera` como `false` para os desativar desde o início; F6 também os limpa. A interface não se move. Consulta o [guia de câmara e apresentação](camera-presentation.md).

O mapa usa os objetos normais `spawn`, `checkpoint` e `goal` e acrescenta:

```json
{"id":"ponte","type":"moving_platform","x":320,"y":460,"end":[480,460],"w":96,"h":12,"speed":75}
{"id":"botao","type":"switch","x":820,"y":474,"gate":"porta"}
{"id":"porta","type":"gate","x":944,"y":352,"w":32,"h":160}
{"id":"lago","type":"water","x":1184,"y":352,"w":320,"h":160,"current":28}
{"id":"leve","type":"gravity_zone","x":1664,"y":240,"w":400,"h":272,"scale":0.38}
```

`end` define o outro extremo do percurso da plataforma. `gate` referencia o ID de uma porta do mesmo mapa. `current` é a velocidade horizontal da corrente, entre -150 e 150. `scale` multiplica a gravidade do jogo, com valores maiores que 0 e até 2; `0.38` corresponde a 38% da gravidade habitual. Estas regras pertencem à cena demonstrativa `examples/environment/scene.py`; podes reutilizar o controlador e os objetos ou adaptá-los ao teu próprio jogo. O solver de colisões e as plataformas móveis continuam a vir do motor Platform2D.

Este laboratório demonstra gravidade **reduzida**, sem inverter chão e teto. Uma inversão completa precisa de superfícies de apoio e colisões próprias para o teto.

A apresentação usa um panorama pintado e uma camada transparente com parallax, descritos no [guia de direção visual](visual-art-direction.md).
A personagem ilustrada e a sua folha de poses estão descritas no [guia de animação](character-animation.md).

A água mostra pequenas bolhas em subida e a zona de gravidade contém pontos luminosos em movimento lento. São animações determinísticas, recortadas à respetiva zona e desenhadas apenas quando esta está visível. F6 também as desliga; não afetam o movimento nem a solução do percurso. A função reutilizável está em `platform2d/rendering/ambient.py`.

Imagens, parallax e paleta são escolhidos por `properties.visual_theme`. Consulta o [guia de temas visuais](visual-themes.md) para criar um tema próprio, usar o tema básico de reserva e distribuir os recursos.
