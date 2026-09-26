# Distribuir o motor e o Resgate — fase 0.24

## Dois públicos, duas distribuições

**Programadores:** `Platform2D-SDK-0.24.0.zip` contém a wheel do motor, código-fonte,
licença MIT, guias, um projeto mínimo e o código do Resgate. O motor instala-se
com pip e pode ser usado sem a campanha Aurora. Os exemplos completos da Aurora
continuam neste repositório de desenvolvimento.

**Jogadores:** `ResgateNaEstacao-1.0.0-Windows-x64.zip` contém o executável, a pasta
`_internal`, instruções e licenças. Extrair tudo e abrir o executável é suficiente.
Não é preciso Python instalado. A compilação não está assinada digitalmente.

Não foi efetuada nenhuma publicação no PyPI, GitHub ou loja. Os ficheiros estão
prontos para serem partilhados pelo autor. A existência da wheel não reserva
o nome Platform2D num serviço público.

## Reconstruir o jogo no Windows

Extrai o código do jogo numa pasta. Usa Python 3.12 x64 e, com caminhos ajustados
às wheels fornecidas, executa:

```powershell
py -3.12 -m venv .build-env
.build-env\Scripts\python.exe -m pip install -r requirements-build.txt
.build-env\Scripts\python.exe -m pip install "C:\wheels\platform2d-0.24.0-py3-none-any.whl"
.build-env\Scripts\python.exe -m pip install .
.build-env\Scripts\python.exe build_windows.py --output dist
```

Para reconstruir a wheel do motor a partir da pasta `engine-source` do SDK:

```powershell
python -m pip install build
python -m build --wheel
```

O processo cria `dist/ResgateNaEstacao`. A receita constrói o jogo instalado num
ambiente sem caminhos para os exemplos da Aurora e inclui explicitamente os
mapas, ícones e sons. O Windows exige uma compilação Windows; outros sistemas
precisam das suas próprias compilações e testes.

Depois da compilação, inclui o README, as licenças e créditos que acompanham
esta distribuição. Ao modificar dependências, atualiza também esses avisos.
O Pygame é incluído sem modificações; o seu código-fonte 2.6.1 e as licenças das
dependências acompanham a distribuição. É permitido reconstruir o jogo com
uma versão modificada compatível dessas bibliotecas. Código do jogo e motor
também são fornecidos para facilitar essa reconstrução.

## Testar antes de partilhar

```powershell
dist\ResgateNaEstacao\ResgateNaEstacao.exe --self-test --data-dir verificacao
dist\ResgateNaEstacao\ResgateNaEstacao.exe --headless --frames 5 --data-dir verificacao-menu
```

A primeira verificação percorre os três setores com ações reais, restaura as
gravações de vitória e escreve `verification.json`. Não basta abrir o menu:
mapas, áudio, imports e gravação podem comportar-se de forma diferente numa
aplicação empacotada.

O pacote desta entrega foi testado neste Windows, a partir de uma pasta diferente
do código-fonte. Isto confirma o funcionamento local da distribuição, não uma
certificação em todos os computadores. Antes de uma publicação mais ampla,
convém experimentar também numa máquina Windows limpa, com outra conta e sem
ferramentas de desenvolvimento.

O motor não recolhe dados nem utiliza uma conta online. O progresso do Resgate
fica em `%LOCALAPPDATA%\ResgateNaEstacao`. O ZIP não inclui saves, preferências,+ambientes virtuais ou caminhos de instalação pessoais como configuração.

Referências: [instalação Python](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/),
[funcionamento do PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html),
[licença do PyInstaller](https://pyinstaller.org/en/stable/license.html) e
[licenças do Pygame](https://github.com/pygame/pygame/tree/2.6.1/docs/licenses).
