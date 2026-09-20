# Incluir vários idiomas no teu jogo

O motor não impõe um idioma. Mantém a lógica, mapas e identificadores estáveis,
colocando os textos visíveis em catálogos separados.

## Estrutura

```text
minha-aventura/
  mygame/
    scene.py
    locales/pt-PT.json
    locales/en.json
    fonts/NotoSans-Regular.ttf
```

Um catálogo contém o nome, a direção, a fonte e as mensagens:

```json
{
  "name": "English",
  "direction": "ltr",
  "font": "NotoSans-Regular.ttf",
  "messages": {
    "title": "My adventure",
    "health": "Health: {current}/{maximum}"
  }
}
```

Conserva as mesmas chaves e parâmetros em todos os idiomas. Não traduzas nomes
de mapas, ações, classes ou formatos de gravação.

## Carregar e desenhar

```python
from pathlib import Path
from platform2d.i18n import Translator, TextRenderer

root = Path(__file__).parent
translator = Translator(root / "locales", "pt-PT")
text = TextRenderer(translator, root / "fonts")

def draw_hud(surface, health):
    text.draw(surface, translator.text("health", current=health, maximum=3), 20)
```

Usa frases completas e parâmetros nomeados. Evita juntar pedaços como
`"Vida: " + str(health)`, pois a ordem muda entre idiomas.

## Integrar com `Game`

Passa o idioma ao painel comum de comandos:

```python
translator.select("en")
game = Game(scene, BINDINGS, title=translator.text("title"), language=translator.language)
```

Guarda a escolha em `user_data_dir("MinhaAventura")`, nunca dentro da pasta
instalada do motor. Uma opção de menu ou `--language en` pode chamar
`translator.select("en")` sem reiniciar a partida. Chama também
`game.set_language("en")` para atualizar os comandos e o áudio comuns; cada
cena continua responsável pelo seu catálogo e pelo título da janela.

## Árabe, chinês e japonês

Para árabe instala o extra opcional:

```powershell
python -m pip install "platform2d[i18n]"
```

O catálogo árabe usa `"direction": "rtl"`. O `TextRenderer` aplica composição
árabe e bidirecional; não inverta caracteres manualmente. Para chinês ou japonês,
inclui uma fonte com os glifos necessários e conserva a respetiva licença. As
fontes Noto estão agora incluídas em `platform2d/fonts`. Podes reutilizá-las:

```python
from platform2d.i18n import FONT_FOLDER
text = TextRenderer(translator, FONT_FOLDER)
```

O campo `font` dos teus catálogos deve corresponder a um dos ficheiros aí
incluídos, como `NotoSans-Regular.ttf`, `NotoNaskhArabic-Regular.ttf`,
`NotoSansCJKsc-Regular.otf` ou `NotoSansCJKjp-Regular.otf`.

A licença MIT do Platform2D não substitui a licença da fonte escolhida.

## Verificar traduções

```python
for language in ("pt-PT", "en"):
    translator.select(language)
    assert not translator.missing(language)
    text.render(translator.text("health", current=2, maximum=3), (255, 255, 255))
```

Testa menus, pausa, vitória, derrota e mensagens longas. Para RTL, confirma o
alinhamento e o texto misto com números ou teclas latinas. O renderizador reduz
o tamanho quando necessário e assinala mensagens que continuam sem caber.

Para plurais, usa variantes por quantidade ou regras CLDR; não acrescentes apenas
um `s`. Mantém códigos BCP 47 como `pt-PT`, `zh-Hans`, `ar` e `ja`.

Consulta o [tutorial de oito idiomas](first-game-tutorial.md) e o [guia geral de
internacionalização](internationalization.md) para um exemplo completo.
