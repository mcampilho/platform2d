# Publicar o Platform2D no GitHub e no PyPI

O GitHub guarda o código, documentação e versões descarregáveis. O PyPI distribui
o **módulo Python**, permitindo `pip install platform2d`. O jogo Windows fica na
Release do GitHub; não é enviado como parte do módulo para o PyPI.

Nada foi publicado automaticamente. A versão preparada é **0.24.0**, sob MIT.
Em 20/09/2026, as consultas às APIs do PyPI e TestPyPI devolveram 404 para
`platform2d`. Isto não reserva o nome nem garante que o registo será aceite.

## 1. Criar o repositório GitHub

Cria uma conta em [GitHub](https://github.com), se necessário. Escolhe **New
repository**, nome `platform2d`, visibilidade Public. Deixa desmarcadas as opções
de gerar README, licença e .gitignore: estes ficheiros já estão preparados.

Abre PowerShell na pasta original do projeto (ou extrai o ZIP
`Platform2D-GitHub-source.zip` e abre a pasta extraída). Com Git instalado:

```powershell
git init -b main
git add .
git status
git diff --cached --stat
git commit -m "Prepare Platform2D 0.24.0 for public release"
git remote add origin https://github.com/TEU_UTILIZADOR/platform2d.git
git push -u origin main
```

Substitui `TEU_UTILIZADOR`. Antes de criar o commit, confirma que a lista contém
código e documentação, sem ambientes virtuais, saves, ficheiros pessoais ou
tokens. O `.gitignore` exclui as pastas locais de trabalho e distribuição.
Se Git pedir identidade, configura `git config user.name "O teu nome"` e
`git config user.email "O teu email GitHub ou endereço noreply"`, e repete o
commit. A autenticação HTTPS pode abrir o navegador através do gestor de
credenciais do Git. Não uses a palavra-passe da conta como token.

No separador **Actions**, verifica o resultado de **Validate Platform2D**.
Este workflow testa o motor, o jogo independente, o tutorial e a instalação
da wheel num ambiente novo num Windows do GitHub. Corrige falhas antes de publicar.

## 2. Ensaiar no TestPyPI com Trusted Publishing

TestPyPI e PyPI têm contas e configurações separadas. Cria/verifica a conta e
configura a autenticação de dois fatores pedida pelo serviço.

No GitHub, abre **Settings → Environments** e cria `testpypi` e `pypi`.
Se a tua conta permitir, configura revisão obrigatória no ambiente `pypi`.

Em [TestPyPI](https://test.pypi.org), abre a gestão de **Publishing / Trusted
Publishers** da tua conta e adiciona um **pending publisher** para um projeto novo:

| Campo | Valor |
|---|---|
| PyPI project name | `platform2d` |
| Owner | O teu utilizador GitHub |
| Repository name | `platform2d` |
| Workflow filename | `publish.yml` |
| Environment name | `testpypi` |

Se o projeto já existir na tua conta, adiciona o publisher nas definições desse
projeto. Se o nome não puder ser usado, escolhe outro antes de publicar e ajusta
o nome em `pyproject.toml`, dependências do jogo/starter, ferramentas e guias.
O nome usado em `import platform2d` pode manter-se.

No GitHub: **Actions → Publish Python package → Run workflow**. Seleciona `main`
e destino `testpypi`. O workflow constrói e verifica apenas os dois pacotes do
motor. A autenticação é temporária, sem guardar um token PyPI no repositório.

Testa numa pasta vazia:

```powershell
py -3.12 -m venv teste
.\teste\Scripts\python.exe -m pip install pygame==2.6.1
.\teste\Scripts\python.exe -m pip install --index-url https://test.pypi.org/simple/ --no-deps platform2d==0.24.0
.\teste\Scripts\python.exe -m platform2d doctor
.\teste\Scripts\python.exe -m platform2d new jogo-teste
Set-Location jogo-teste
..\teste\Scripts\python.exe -m mygame
```

Pygame é obtido primeiro do PyPI normal; o motor vem isoladamente do TestPyPI.

## 3. Publicar no PyPI real

Repete o registo do pending publisher em [PyPI](https://pypi.org), desta vez
com **Environment name `pypi`**. Os restantes campos mantêm-se.

Depois de os testes passarem e de reveres os ficheiros:

```powershell
git tag -a v0.24.0 -m "Platform2D 0.24.0"
git push origin v0.24.0
```

Executa **Publish Python package** novamente, selecionando a **tag `v0.24.0`**
no seletor de referência e o destino **`pypi`**. O workflow rejeita publicação
de produção se a tag não corresponder à versão de `pyproject.toml`.

Após sucesso, confirma numa nova instalação:

```powershell
py -3.12 -m venv publico
.\publico\Scripts\python.exe -m pip install platform2d==0.24.0
.\publico\Scripts\python.exe -m platform2d doctor
```

Só depois disso anuncia aos utilizadores `pip install platform2d`.
Não podes substituir ficheiros de uma versão já enviada: alterações posteriores
precisam de nova versão, atualização das referências e nova tag.

## 4. Criar a Release no GitHub

Abre **Releases → Draft a new release**, escolhe a tag `v0.24.0`, título
`Platform2D 0.24.0` e usa o resumo de `CHANGELOG.md`. Anexa:

- `artifacts/releases/Platform2D-SDK-0.24.0.zip`;
- `artifacts/releases/ResgateNaEstacao-1.0.0-Windows-x64.zip`;
- wheel e `.tar.gz` do motor em `artifacts/publication/`;
- `artifacts/releases/SHA256SUMS.txt`.

O GitHub já fornece o código-fonte da tag automaticamente. Explica na descrição
que o executável é Windows x64, enquanto o SDK requer Python e Pygame. Publica
a Release depois do ensaio noutro computador descrito em `second-computer-test.md`.

## Alternativa manual ao workflow

Na raiz, usa uma pasta de saída vazia. Estes comandos não incluem a wheel do jogo:

```powershell
python -m pip install build twine
python -m build --outdir artifacts/publication
python -m twine check --strict artifacts/publication/*
python tools/check_public_package.py artifacts/publication
python -m twine upload --repository testpypi artifacts/publication/platform2d-0.24.0*
# Apenas depois de confirmar o ensaio:
python -m twine upload artifacts/publication/platform2d-0.24.0*
```

Quando pedido, usa `__token__` como utilizador e o token do serviço como
palavra-passe. Não escrevas tokens nos comandos, ficheiros do projeto ou chat.
Esta alternativa dispensa Trusted Publishing; não é preciso configurar ambas.

## Referências oficiais

- [Enviar código local para GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)
- [Criar Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Empacotar projetos Python](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
