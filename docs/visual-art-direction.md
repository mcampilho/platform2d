# Direção visual do Mundo Vivo

O laboratório ambiental usa duas imagens originais geradas com a ferramenta integrada **ImageGen** e guardadas no próprio projeto:

| Camada | Ficheiro | Movimento |
|---|---|---|
| Paisagem distante | `examples/environment/assets/astral-greenhouse-bg.png` | 27% do movimento horizontal da câmara |
| Vegetação e observatório próximos | `examples/environment/assets/observatory-foreground.png` | 55% do movimento horizontal da câmara |
| Terreno, personagem e objetos | desenho e animação do jogo | 100% do movimento da câmara |

A camada próxima tem transparência real. É desenhada atrás das plataformas e da personagem para não esconder os elementos jogáveis. Um filtro escuro subtil sobre a paisagem ajuda a distinguir a geometria. Blocos, plataforma, interruptor, porta, água e gravidade receberam cores e formas coerentes com as imagens. As sombras e partículas continuam opcionais com F6.

Para trocar a arte no teu mapa, coloca os novos PNG em `examples/environment/assets/` e indica os nomes simples de ficheiro em `properties.background_image` e `properties.foreground_image`. O primeiro deve cobrir todo o ecrã; o segundo deve ter canal alfa e deixar livre a área central. `platform2d/rendering/panorama.py` redimensiona cada imagem à altura do ecrã, desloca-a com a câmara e otimiza o formato após a abertura da janela. Não são necessárias imagens com a largura total do mapa.

Prompts usados na ferramenta integrada, sem pedir imitação de qualquer jogo ou artista:

**Paisagem distante**

> Use case: stylized-concept. Asset type: original painted background for a 2D side-scrolling platform game, behind playable tiles across a wide level. Scene: an ancient overgrown astronomical greenhouse built into a mountain valley, distant layered indigo cliffs, turquoise waterfalls, luminous moss, delicate copper observatory arches, soft mist and dusk sky. Style: original hand-painted game environment, expressive shapes, rich brush texture, cohesive art direction, high visual quality, readable silhouettes, atmospheric depth. Composition: panoramic wide landscape, horizon and dramatic distant structures in upper and middle thirds, lower third subdued and uncluttered so characters/platforms stay legible; smooth detail density across entire width for horizontal scrolling. Palette: deep midnight blue, muted teal, violet shadows, restrained warm amber accents. Constraints: background only; no characters, no user interface, no text, no logos, no watermark. Do not imitate any named game or artist.

**Camada próxima**

> Use case: stylized-concept. Asset type: transparent parallax foreground strip for an original 2D side-scrolling fantasy platform game. Subject: sparse hanging vines, fern fronds, weathered copper observatory railings and dark botanical silhouettes along only the lower edge and far left/right edges. Composition: ultra-wide horizontal transparent canvas; leave the center 70% and upper 60% mostly empty/transparent so a player and platforms remain visible; organic elements taper into transparency; no ground plane. Style: painterly illustrated game asset with deep navy, muted teal, restrained copper accents, cohesive with an overgrown astronomical greenhouse at dusk. Lighting: subtle backlit rim highlights. Constraints: genuine transparent alpha background, no opaque sky or scenery, no characters, no UI, no text, no logo, no watermark, no imitation of named games or artists.

A personagem usa agora uma folha de oito poses ilustradas, descrita no [guia de animação](character-animation.md). Para um jogo com identidade visual completa, efeitos, tipografia e interfaces precisam de seguir a mesma direção de arte e de ser revistos em conjunto.

O laboratório ambiental usa também uma interface inspirada no observatório: painéis azul-escuros com rebordo de cobre, instrução do sector ao centro e indicadores compactos de progresso, dash e tentativas. Os ecrãs de pausa e conclusão seguem agora a mesma paleta e mostram o avanço pelos quatro sectores. Esta interface pertence apenas ao exemplo `examples/environment/scene.py`; as outras demonstrações mantêm as suas próprias apresentações. A escolha de desenhar os ornamentos com formas simples evita carregar imagens adicionais ou alterar a física.

O terreno e a plataforma móvel usam agora pequenas superfícies de pedra e metal desenhadas uma vez e guardadas em cache em `examples/environment/terrain_view.py`. As juntas, fissuras, rebites e vegetação são determinísticos; a câmara só desloca as superfícies prontas. Este acabamento é apenas visual: o mapa e as caixas de colisão continuam iguais.

Os objetos interativos seguem a mesma linguagem visual em `examples/environment/object_view.py`: checkpoint em forma de marco, interruptor de cobre, portão com barras e saída em arco. Os estados são visíveis sem depender só da cor: o interruptor deixa de mostrar a tecla E quando ativo, e a abertura da porta fica transparente para mostrar que se pode atravessar. A colisão da porta continua a ser comandada pela cena.
