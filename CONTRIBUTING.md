# Contribuir para Platform2D

Obrigado por ajudares a melhorar o motor. Começa por comunicar um problema ou
explicar a alteração pretendida numa issue do repositório.

## Preparar o ambiente

Usa Python 3.12 para reproduzir o ambiente de referência:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[i18n]"
.venv\Scripts\python.exe -m unittest discover -s tests
```

Instala `games/resgate` no mesmo ambiente para testar o jogo independente:

```powershell
.venv\Scripts\python.exe -m pip install -e games/resgate
.venv\Scripts\python.exe -m unittest discover -s games/resgate/tests
.venv\Scripts\python.exe -m resgate --self-test --data-dir artifacts/resgate-check
```

## Propor uma alteração

Cria uma branch, faz uma alteração com âmbito claro e abre um pull request.
Explica o problema, o comportamento resultante e como o verificaste. Para uma
correção de física ou regras, inclui um teste que reproduza o problema. Para
uma alteração visual, inclui uma captura e verifica que não muda a simulação.

O motor não importa `examples` nem `games`. As regras de um jogo ficam no seu
projeto. Mantém desenho e simulação separados e preserva o contrato de gravação;
se mudares esse contrato, valida ou rejeita explicitamente versões anteriores.

Consulta [internacionalização](docs/internationalization.md) para contribuir
com traduções. Documentação atual: português de Portugal. Código e nomes de API:
inglês, seguindo os módulos existentes. Evita alterações de formatação em
ficheiros sem relação com a tarefa. As contribuições para o código e recursos
originais deste projeto são feitas sob a licença MIT incluída.

Não incluas ambientes virtuais, saves pessoais, tokens, pastas de compilação ou
ZIPs num commit. Os ficheiros de distribuição pertencem às Releases.
