# Internacionalizar Platform2D e os teus jogos

O tutorial, o Resgate na Estação, a campanha Aurora, os editores, os comandos e o áudio
têm português de Portugal, inglês, espanhol, francês, alemão, chinês simplificado,
árabe e japonês. O Resgate inclui menus, HUD, nomes de níveis, portas, ar, oxigénio,
ameaça, briefings, confirmações e mensagens de erro. A campanha inclui menus,
nomes dos mapas e textos dos treze níveis. Os editores incluem ferramentas, menus,
perfis e diagnósticos frequentes. Outros exemplos independentes e a documentação
técnica ainda não foram inteiramente traduzidos.
Estas traduções iniciais devem ser revistas por falantes de cada idioma.

## Experimentar

Na raiz do projeto, instala as dependências opcionais de árabe:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[i18n]"
.venv\Scripts\python.exe tutorials/first_game/main.py --language en
```

Também podes abrir `Jogar-Tutorial.cmd`. **F4** percorre os oito idiomas sem
alterar posição, vida, recolhas ou pausa. A escolha feita com F4 fica em
`Platform2D-Tutorial/language.json` na pasta de dados do utilizador.
`--language` tem prioridade; testes headless não alteram a preferência.

Para o Resgate, usa o ambiente Python 3.13 que já tens a funcionar. Na raiz do
repositório, instala motor e jogo na mesma operação para resolver a dependência
local sem procurar o motor no PyPI:

```powershell
uv pip install --python .venv-resgate313\Scripts\python.exe -e ".[i18n]" -e games\resgate
.venv-resgate313\Scripts\python.exe -m resgate --language fr
.venv-resgate313\Scripts\python.exe -m resgate --language ar
```

Para jogar a campanha ou abrir os editores no idioma escolhido:

```powershell
.venv\Scripts\python.exe -m examples.campaign --language ja
.venv\Scripts\python.exe -m examples.editor --profile campaign --language ar
.venv\Scripts\python.exe -m examples.editor --language en
```

Usa o caminho do teu ambiente se tiver outro nome. Para criar um novo ambiente,
especifica a versão: `uv venv .venv-resgate313 --python 3.13`. O ambiente de CI
continua em Python 3.12. A escolha do Resgate é feita ao iniciar; não altera a
gravação. F3 abre o painel traduzido, incluindo conflitos de teclas e botões.

| Idioma | Código |
|---|---|
| Português de Portugal | `pt-PT` |
| Inglês | `en` |
| Espanhol | `es` |
| Francês | `fr` |
| Alemão | `de` |
| Chinês simplificado | `zh-Hans` |
| Árabe | `ar` |
| Japonês | `ja` |

O tutorial usa teclas fixas e instruções traduzidas. O painel comum F3 fica
desativado neste exemplo. O `Game` e `ControlsPanel` aceitam `language="en"`
ou qualquer um dos oito códigos. Outros jogos precisam de catálogo próprio e de
passar o idioma ao ponto de entrada.

## Separar código e tradução

`platform2d/i18n.py` fornece `Translator` e `TextRenderer`. Cada jogo mantém os
seus catálogos e fontes; o motor não depende dos textos do tutorial. Não há
uma variável global de idioma a interferir com outros jogos ou testes.

Cada JSON em `tutorials/first_game/locales` contém nome, direção, fonte e
`messages`. Exemplo abreviado:

```json
{
  "name": "English",
  "direction": "ltr",
  "font": "NotoSans-Regular.ttf",
  "messages": {"health": "Health: {current}/{maximum}"}
}
```

O código usa `translator.text("health", current=2, maximum=3)`. Mantém chaves
e parâmetros iguais e traduz apenas os valores. Usa frases completas: o
tradutor pode reposicionar os parâmetros. IDs de mapas, ações, classes e
chaves funcionais das gravações não são traduzidos.

Uma tradução em falta usa português. Chaves inexistentes e parâmetros
incompatíveis geram erros explícitos. O verificador exige cobertura completa
dos oito idiomas. Códigos regionais procuram primeiro correspondência exata,
depois a única variante disponível da língua; isto não cria outras traduções
regionais. No tutorial, o chinês disponibilizado é apenas simplificado.

## Fontes, direção e espaço

As fontes comuns Noto estão agora em `platform2d/fonts`, incluídas na wheel do
motor, com licenças OFL e origens identificadas por commit e SHA-256. O tutorial
conserva também as suas cópias. Não há dependência de fontes instaladas ou de
pastas do tutorial para executar o Resgate. As fontes chinesa e japonesa ocupam
cerca de 16 MB cada. O código mantém a licença MIT; as fontes conservam OFL-1.1.

Para árabe, `arabic-reshaper` liga as formas das letras e `python-bidi` aplica
o algoritmo bidirecional, preservando números e teclas latinas. O texto alinha
à direita. Não invertas letras manualmente nem espelhes a física ou os controlos.
Esta solução serve os rótulos de uma linha do tutorial; parágrafos, edição de
texto e outros scripts exigem composição mais completa.

`TextRenderer` mede o texto e reduz o tamanho até 12 quando necessário. Se não
couber, gera erro para aumentar a área ou dividir a frase. Não corta palavras
nem comprime horizontalmente os caracteres.

## Acrescentar ou rever um idioma

1. Copia um catálogo completo, atribui um código e traduz os valores.
2. Mantém os parâmetros entre chavetas e indica a fonte e direção.
3. Acrescenta o código a `LessonScene.LANGUAGES` e às opções `--language` de
   `main.py`; inclui uma fonte e respetiva licença.
4. Executa as verificações e revê as capturas:

```powershell
.venv\Scripts\python.exe tools/check_tutorial_languages.py
.venv\Scripts\python.exe tools/check_resgate_languages.py
.venv\Scripts\python.exe tools/check_campaign_languages.py
.venv\Scripts\python.exe tools/check_editor_languages.py
.venv\Scripts\python.exe -m unittest discover -s tests
.venv\Scripts\python.exe tutorials/first_game/main.py --language ar --verify
```

O primeiro comando verifica mensagens, caracteres reais das fontes e 24
combinações de lição/estado por idioma. As imagens ficam em `artifacts/i18n`.
O GitHub executa também esta verificação. Confirma manualmente legibilidade,
sentido das traduções e mudança de idioma; testes não fazem revisão linguística.

Para manter as traduções, edita `translations/common.tsv`, `resgate.tsv`,
`campaign.tsv` e `editor.tsv`: cada linha tem uma chave e oito colunas separadas
por tabulações, na ordem do cabeçalho. Executa `python tools/build_ui_catalogs.py`
para gerar os JSON nas pastas `locales` dos componentes.
Inclui no commit as tabelas e os JSON gerados. Os programas carregam apenas os JSON;
a ferramenta de geração não é necessária no computador do jogador.

## Migrar o resto do projeto

Falta migrar os textos dos outros exemplos independentes, alguns erros de
ficheiros personalizados que surgem no editor, documentação e página pública.
Usa catálogos separados
por componente e IDs estáveis. Começa a documentação internacional com um
README inglês, depois guias por idioma identificando a versão traduzida.

O tutorial evita plurais e datas. Quando necessários, usa regras de cada língua
(por exemplo, CLDR através de Babel), sem pressupor apenas singular/plural.
Planeia formatos de números, quebra de linhas CJK e fontes de reserva.

Esta internacionalização faz parte da versão 0.24.0. Os catálogos do tutorial,
Resgate, campanha e editores são verificados no CI nos oito idiomas. Exemplos
independentes que não usam estes catálogos podem ser migrados gradualmente com
o mesmo modelo, sem alterar as chaves já publicadas.

## Referências

- [Texto e fontes no Pygame](https://www.pygame.org/docs/ref/font.html)
- [Arabic Reshaper](https://github.com/mpcabd/python-arabic-reshaper)
- [Python BiDi](https://python-bidi.readthedocs.io/en/latest/)
- [Fontes Noto CJK](https://github.com/notofonts/noto-cjk)
