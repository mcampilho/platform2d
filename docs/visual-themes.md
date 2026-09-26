# Temas visuais reutilizáveis

Um tema visual reúne a identidade gráfica sem alterar física, objetivos ou mapas. O motor fornece `platform2d.rendering.theme`, que valida o manifesto, resolve os recursos e disponibiliza uma paleta com valores de reserva.

## Manifesto

Cria um ficheiro como `meu-tema.theme.json` ao lado das imagens do jogo:

```json
{
  "format": "platform2d.theme",
  "version": 1,
  "id": "meu-tema",
  "name": "O Meu Tema",
  "palette": {
    "ink": [8, 15, 28],
    "panel": [21, 39, 47],
    "line": [83, 97, 81],
    "accent": [153, 120, 78],
    "highlight": [215, 178, 106],
    "text": [229, 226, 204],
    "muted": [164, 188, 185]
  },
  "assets": {
    "background": "fundo.png",
    "foreground": "primeiro-plano.png",
    "character": "personagem.png"
  },
  "sprites": {
    "guardian": {
      "image": "guardiao-atlas.png",
      "frame_size": [60, 72],
      "clips": {
        "idle": {"frames": [0], "fps": 1},
        "walk": {"frames": [1, 2, 3, 4], "fps": 8}
      },
      "anchor": [0.5, 1.0],
      "directional": true
    }
  },
  "parallax": {"background": 0.27, "foreground": 0.55}
}
```

Os nomes dos recursos não podem conter pastas. Esta restrição mantém todos os ficheiros dentro da pasta de recursos escolhida. O carregamento confirma o formato, as cores RGB, os fatores entre 0 e 1 e a existência das imagens antes de iniciar o jogo.

`sprites` é opcional. Cada atlas usa uma grelha regular definida por
`frame_size`; os índices são contados da esquerda para a direita e de cima para
baixo. Um clip define a sequência, velocidade e, opcionalmente, `"loop": false`.
`anchor` indica o ponto do desenho colocado sobre a posição do mundo: `[0.5, 1]`
é o centro dos pés. Com `directional: true`, o motor prepara também a direção
espelhada e ajusta a âncora automaticamente.

No mapa, basta indicar:

```json
"properties": {"visual_theme": "meu-tema.theme.json"}
```

O exemplo completo é `examples/environment/assets/observatory.theme.json`. `EnvironmentScene` chama:

```python
theme = load_theme(manifesto, pasta_dos_recursos)
cor = theme.color("accent")
fundo = theme.assets["background"]

from platform2d.rendering.sprite_animation import SpriteAtlas
guardiao = SpriteAtlas.from_spec(theme.sprites["guardian"])
guardiao.draw(ecra, (x, chao_y), "walk", tempo, direcao)
```

`load_theme(None)` devolve sempre o tema básico do Platform2D, sem imagens obrigatórias. Assim, um novo jogo pode começar apenas com formas e cores e acrescentar arte mais tarde. Campos de paleta omitidos também recebem os valores básicos.

## Criar e verificar pela linha de comandos

Cria uma pasta nova com um manifesto completo e um pequeno guia:

```powershell
python -m platform2d theme new themes\jardim-lunar --id jardim-lunar --name "Jardim Lunar"
```

Depois de copiares as imagens para essa pasta e preencheres `assets`, valida o tema:

```powershell
python -m platform2d theme check themes\jardim-lunar\jardim-lunar.theme.json
```

Para gerar também uma imagem de apresentação:

```powershell
python -m platform2d theme check themes\jardim-lunar\jardim-lunar.theme.json --preview themes\jardim-lunar\preview.png
```

O diagnóstico mostra as dimensões e a transparência de cada recurso, valida os
fotogramas referidos e rejeita atlas que não sejam divisíveis pelo tamanho da
célula. A pré-visualização combina fundo, primeiro plano, personagem, paleta e
uma amostra de cada sprite animado sem ser necessário escrever uma cena.

## Recarregar durante o jogo

O projeto criado por `platform2d new` e o laboratório Mundo Vivo associam **F7** a `reload_theme`. Guarda o manifesto ou substitui uma imagem e prime F7 para aplicar o tema sem reiniciar a partida. O carregamento constrói primeiro todos os recursos novos; só depois substitui o tema visível. Se o JSON ou uma imagem estiverem inválidos, o último tema válido permanece ativo e o jogo mostra a causa do erro.

Para acrescentar esta capacidade a outra cena, usa `ThemeHandle`: `reload()` devolve `True` quando aceita a nova versão e conserva `current` quando encontra um erro. Cenas que transformem imagens em panoramas, folhas de animação ou outras estruturas devem seguir o padrão de `EnvironmentScene.reload_visual_theme`: construir um conjunto candidato completo antes de o instalar.

## Editor e campanha

Em **Missão / ambiente → Ambiente da sala**, o Atelier inclui **Observatório** juntamente com Estação, Jardins, Glacial e Reator. A pré-visualização F5 usa logo o tema escolhido. O nível **Vale das Três Luas** demonstra esta escolha dentro da campanha.

Os temas procedimentais da campanha usam a propriedade `theme`. Um jogo pode combinar essa escolha com um manifesto mais rico na sua própria cena: `theme` identifica o estilo lógico do mapa; `visual_theme` aponta para os recursos concretos.

As propriedades visuais não fazem parte da identidade de jogabilidade de uma gravação. Trocar a paleta, o manifesto ou as imagens conserva o progresso. Alterações a objetos, capacidades, movimento e restantes regras continuam a tornar uma gravação incompatível. As gravações criadas antes desta separação são aceites quando a única diferença é o tema e são atualizadas na gravação automática seguinte.

## Distribuição

Inclui o manifesto e todas as imagens referidas no pacote ou na pasta do jogo. Mantém nomes relativos simples e testa a instalação construída, porque o validador rejeita um pacote onde falte uma imagem. O tema não deve guardar caminhos absolutos do computador de desenvolvimento.

Arte, fontes e áudio podem ter licenças diferentes do código MIT. Distribui apenas recursos que possas licenciar e acrescenta os respetivos créditos ao jogo.
