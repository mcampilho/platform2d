# Desenvolver jogos com Platform2D 0.24

Platform2D é um módulo Python instalável, construído sobre Pygame. Fornece ciclo
de jogo com passo fixo, input e gamepad, física, personagens, câmaras, áudio,
combate, mecanismos e ferramentas de edição. Cada jogo define as suas regras,
mapas, recursos, menus e condições de vitória num projeto separado.

O motor e os recursos originais incluídos são distribuídos sob licença **MIT**.
Podes usá-los, modificá-los e distribuí-los, incluindo em jogos comerciais,
mantendo o aviso de copyright e a licença. O teu jogo pode ter outra licença.
Pygame e as suas dependências conservam as respetivas licenças; a licença MIT
do motor não as substitui. [Texto oficial MIT](https://opensource.org/license/mit)
e [licença do Pygame](https://github.com/pygame/pygame/blob/2.6.1/README.rst#license).

As fontes Noto incluídas para a interface multilingue usam OFL-1.1; conserva
os avisos em `platform2d/fonts/OFL-*.txt`. O código continua MIT. Os metadados
do pacote indicam ambas as licenças porque a wheel contém também as fontes.

## Instalar a distribuição fornecida

Recomenda-se **Python 3.12 de 64 bits** para reproduzir o ambiente testado no
Windows. O pacote declara Python 3.10 ou superior; outras combinações dependem
também da disponibilidade do Pygame e não foram verificadas nesta entrega.

Descarrega a wheel do motor de uma publicação do autor. No terminal, dentro de
uma pasta de trabalho:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install "C:\caminho\platform2d-0.24.0-py3-none-any.whl"
.venv\Scripts\python.exe -m platform2d doctor
.venv\Scripts\python.exe -m platform2d new meu-jogo --name "A minha aventura"
cd meu-jogo
..\.venv\Scripts\python.exe -m mygame
```

Substitui o caminho da wheel pelo local onde a guardaste. O pip instala a
dependência `pygame==2.6.1`; essa primeira instalação precisa de internet,
salvo se também disponibilizares as wheels das dependências compatíveis com
o Python e o sistema do destinatário. Não é necessário ativar o ambiente no
PowerShell quando usas os caminhos explícitos acima.

**O pacote não foi publicado no PyPI nesta entrega.** Não uses simplesmente
`pip install platform2d` para obter este projeto: esse nome no índice público
não foi reservado. Em 20/09/2026, as APIs do PyPI e TestPyPI não encontraram um
projeto com esse nome, o que não garante disponibilidade futura. A wheel
fornecida identifica a distribuição correta. A publicação exige um nome aceite; o nome de
distribuição no índice pode diferir de `import platform2d`.

O uso de ambientes virtuais e instalação de wheels locais segue o
[guia oficial de instalação Python](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/).

## O que alterar no projeto gerado

`mygame/scene.py` contém um jogo mínimo completo: movimento, salto, uma recolha
e uma saída. `mygame/__main__.py` configura a janela e as teclas. O ficheiro
`mygame/theme.json` controla a paleta e já pode ser verificado com
`python -m platform2d theme check mygame/theme.json --preview theme-preview.png`.
`pyproject.toml` declara o motor como dependência. Muda o nome de distribuição,
o título e o ID de dados do utilizador quando criares o teu jogo.

O comando `new` só aceita uma pasta inexistente: não substitui trabalho teu.
Não copies as pastas `platform2d` ou `examples` para o novo projeto.

## Contrato mínimo de uma cena

Uma cena fornece `update(dt, actions)` para simulação e `draw(surface, alpha)`
para desenho. O motor chama a simulação a 60 passos por segundo e usa `alpha`
para interpolar posições. O desenho não deve avançar relógios nem aplicar dano.

```python
from platform2d.core.game import Game
from platform2d.actors.character import Character
from platform2d.actors.controller import ArcadeController, Movement
from platform2d.physics.body import Body

player = Character(Body(80, 100), ArcadeController(Movement(speed=210)))
# Na cena: player.update(dt, actions, colliders)
# No desenho: x, y = player.body.interpolated(alpha)
```

`Game` fornece à cena áudio (`scene.audio`) e formatação de comandos. F3 abre
o painel de comandos; F10/F11/F12 controlam o áudio. Define a propriedade
`paused` quando a cena estiver parada. Fecha a janela para sair.

## Escolher os módulos necessários

| Necessidade | Módulos |
| --- | --- |
| Teclado e gamepad | `core.input`, `core.control_settings` |
| Movimento e colisões | `actors.character`, `actors.controller`, `physics.collision` |
| Água e salto duplo | `actors.exploration` |
| Voo e bordas | `actors.traversal` |
| Câmaras e mapas | `world.camera`, `world.tilemap` |
| Vida, projéteis e espada | `gameplay.combat`, `gameplay.projectiles`, `gameplay.sword` |
| Caixas e peso | `gameplay.cargo` |
| Áudio e apresentação | `audio`, `rendering` |
| Dados por utilizador | `paths.user_data_dir` |
| Editor de mapas | `tools.editor_model`, `tools.level_editor` |

As cenas da campanha Aurora são demonstrações, não fazem parte da API do
pacote. O editor recebe uma fábrica de cenas do teu jogo: não conhece regras
arbitrárias por si só. O formato JSON suportado e a validação devem corresponder
à tua cena. Para um jogo novo, começa com o modelo gerado e adiciona módulos
quando precisares deles; não é necessário usar todos.

O projeto separado `Resgate na Estação` demonstra três níveis, recursos
empacotados, menus, gravação e distribuição sem importar `examples`.

## Recursos, gravações e versões

Inclui mapas, imagens e sons no pacote do jogo, declara-os em
`tool.setuptools.package-data` e carrega-os relativamente a `__file__` ou com
`importlib.resources`. Guarda preferências e progresso em
`user_data_dir('IDDoTeuJogo')`, nunca junto do executável instalado.

Nas tuas dependências, fixa uma versão testada (`platform2d==0.24.0`) ou um
intervalo menor (`platform2d>=0.24,<0.25`). Enquanto o motor estiver em 0.x,
não se promete compatibilidade automática entre versões menores. Testa os
teus percursos e gravações antes de atualizar.

## Partilhar o motor ou o jogo

Para programadores, partilha o ZIP SDK: wheel, código-fonte, licença e guias.
Para jogadores, partilha a pasta Windows completa do jogo, incluindo `_internal`
e licenças. O jogador não precisa de Python. Para reconstruir o jogo, utiliza
o seu código-fonte e a receita de distribuição fornecida.

PyInstaller produz uma aplicação específica do sistema onde é construído;
a versão Windows não é uma aplicação macOS ou Linux. Nesta entrega, a opção
de pasta completa facilita verificar recursos e bibliotecas. [Documentação
oficial do PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).
