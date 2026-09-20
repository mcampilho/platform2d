# Platform2D

Motor modular para jogos de plataformas em **Python + Pygame**, desenvolvido
por etapas para aprender a construir jogos. Versão preparada: **0.23.0**.
Licença **MIT**, permitindo utilização, modificação e distribuição, incluindo
jogos comerciais, nos termos da licença.

Inclui física e colisões, vários controladores, animação, câmaras e parallax,
combate, áudio, inventário, mecanismos, progresso e ferramentas de edição.
A campanha de demonstração reúne 12 níveis com diferentes estilos. O jogo
**Resgate na Estação** demonstra um projeto independente com três níveis.

## Começar

Recomendado para acompanhar os tutoriais: Python 3.12 e Windows. O pacote declara
Python >=3.10; a verificação principal preparada usa Python 3.12 em Windows.
Outros sistemas e versões ainda precisam de validação específica.

Com o código descarregado, abre o terminal nesta pasta:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m platform2d doctor
.venv\Scripts\python.exe -m platform2d new meu-jogo --name "O meu jogo"
Set-Location meu-jogo
..\.venv\Scripts\python.exe -m mygame
```

A instalação inicial necessita de Internet para obter Pygame. Também podes
instalar a wheel do SDK: consulta o [guia de utilização](docs/using-platform2d.md).
O pacote está preparado para publicação, mas este repositório não pressupõe
que já esteja disponível no PyPI.

## Aprender e experimentar

- [Primeiro jogo: seis lições executáveis](docs/first-game-tutorial.md).
- [Tutorial em oito idiomas e internacionalização](docs/internationalization.md).
- [Internacionalizar um jogo criado com a framework](docs/localizing-your-game.md).
- [Como funciona o jogo independente](docs/learning-independent-game.md).
- [Instalação e API do motor](docs/using-platform2d.md).
- [Histórico das entregas, exemplos e controlos](docs/project-history.md).
- [Distribuir os teus próprios jogos](docs/distributing-platform2d.md).

Executa `tutorials/first_game/main.py` com o Python do ambiente para abrir o
pequeno jogo do tutorial. Os ficheiros `Jogar-*.cmd` e `Editor-*.cmd` abrem as
várias demonstrações e editores; coloca o nome entre aspas se contiver espaços.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `platform2d/` | Motor instalável e recursos próprios |
| `examples/` | Campanhas e exemplos de funcionalidades |
| `games/resgate/` | Jogo independente, com pacote e testes próprios |
| `tutorials/first_game/` | Seis lições cumulativas |
| `tests/` | Testes automáticos do motor e tutorial |
| `docs/` | Guias de aprendizagem e distribuição |
| `tools/` | Verificações e preparação de entregas |

## Contribuir e publicar

Consulta [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md) e
[LICENSE](LICENSE). Não é necessário alterar o motor para criar um jogo: o
starter gera um projeto separado que o importa como dependência.

- [Enviar para GitHub e publicar no PyPI, passo a passo](docs/publishing-github-pypi.md).
- [Roteiro de teste noutro computador](docs/second-computer-test.md).

O workflow `Validate Platform2D` verifica testes, tutorial e pacotes num Windows
do GitHub. `Publish Python package` permite ensaiar no TestPyPI e publicar no
PyPI, mediante configuração prévia da conta pelo responsável do projeto.
