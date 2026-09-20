# Resgate na Estação

Um jogo independente, com três setores: recuperar equipamento no cais, ativar
válvulas num reservatório inundado e alcançar a nave durante uma evacuação.
Inclui início, instruções, pausa, checkpoints, gravação e final.

## Jogar no Windows

Extrai **toda** a pasta do ZIP e abre `ResgateNaEstacao.exe`. Conserva a pasta
`_internal` junto do executável. Não é necessário instalar Python ou Pygame.

Setas/A/D movem; Espaço/Z salta; Cima/W nada para cima; Baixo/S mergulha.
Enter confirma; P pausa; R regressa ao checkpoint; F3 configura comandos;
F6 guarda; F9 pede confirmação para carregar. F10 silencia; F11/F12 ajustam o som.
O jogo completo e o painel de comandos podem usar outro idioma com `--language en`,
`es`, `fr`, `de`, `zh-Hans`, `ar` ou `ja`; o idioma predefinido é `pt-PT`.

O jogo guarda automaticamente nos checkpoints e no fim de cada setor.
Continuar regressa ao checkpoint; o oxigénio e a perseguição são reiniciados.
Nova missão pede confirmação antes de substituir uma gravação existente.

Gravações e preferências ficam em `%LOCALAPPDATA%\ResgateNaEstacao`, fora da
pasta instalada. Guarda essa pasta para fazer uma cópia de segurança. O ZIP
nunca inclui as gravações do autor. O executável não tem assinatura digital;
o Windows pode apresentar um aviso de aplicação desconhecida.

## Desenvolver a partir do código

No repositório completo, instala motor e jogo juntos no ambiente que escolheste:

```powershell
uv pip install --python .venv-resgate313\Scripts\python.exe -e ".[i18n]" -e games\resgate
.venv-resgate313\Scripts\python.exe -m resgate --language ja
```

As fontes vêm do motor instalado; não é preciso copiar ficheiros do tutorial.
As traduções próprias do jogo ficam em `resgate/locales`. Os ZIPs Windows de
entregas anteriores não recebem alterações do código editável: esta fase
necessita de um executável reconstruído.

Com Python 3.12 de 64 bits, cria um ambiente virtual e instala a wheel fornecida
do motor. Depois, na pasta que contém este `pyproject.toml`:

```powershell
python -m pip install -e .
python -m resgate
```

O motor é uma dependência externa. Não copies `platform2d` nem `examples` para
este projeto. As regras estão em `resgate/scene.py`; os mapas e o ícone são
recursos próprios em `resgate/assets`. Podes instalar também a wheel do jogo.

Para verificar os três percursos automaticamente:

```powershell
python -m resgate --self-test --data-dir verificacao
```

A verificação usa gravações temporárias, gera imagens e um relatório. Não
altera a partida normal. `--headless --frames 3` permite testar só o arranque.

Código, mapas e arte procedural deste jogo: licença MIT, conforme `LICENSE`.
Platform2D: Miguel e colaboradores. Pygame e SDL: respetivos autores; as suas
licenças são independentes e acompanham a distribuição Windows.
