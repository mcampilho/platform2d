# Testar noutro computador

Estado: os testes locais passaram; o teste humano num segundo computador ainda
não foi realizado. O workflow `Validate Platform2D` também só correrá depois
de enviares o repositório para o GitHub. Um teste automático sem janela não
confirma áudio, resposta do teclado, apresentação ou avisos do Windows.

## Para alguém que só quer jogar (Windows x64)

1. Copia `ResgateNaEstacao-1.0.0-Windows-x64.zip` para outro computador.
2. Extrai **todo** o ZIP para uma pasta; não executes dentro do ZIP.
3. Abre `ResgateNaEstacao/ResgateNaEstacao.exe`. Não é preciso instalar Python.
4. Confirma que o menu aparece, inicia o jogo e experimenta os controlos indicados.
5. Confirma movimento, salto, som, pausa e regresso ao jogo.
6. Experimenta guardar/carregar e fecha/volta a abrir a aplicação.
7. Joga os três níveis e confirma a conclusão da campanha.

O executável não tem assinatura digital. Regista qualquer aviso que apareça;
não é necessário desativar o antivírus para efetuar este teste.

Também podes verificar a lógica automaticamente, no terminal da pasta extraída:

```powershell
.\ResgateNaEstacao\ResgateNaEstacao.exe --self-test --data-dir "$env:TEMP\Platform2D-check"
```

O resultado fica em `verification.json` dentro dessa pasta. Este comando usa
dados de teste separados dos progressos normais do jogador.

## Para alguém que quer desenvolver

1. Instala Python 3.12 de 64 bits e extrai o SDK.
2. No terminal da pasta do SDK, executa:

```powershell
py -3.12 -m venv ambiente
.\ambiente\Scripts\python.exe -m pip install .\wheels\platform2d-0.24.0-py3-none-any.whl
.\ambiente\Scripts\python.exe -m platform2d doctor
.\ambiente\Scripts\python.exe -m platform2d new primeiro-jogo --name "O meu jogo"
Set-Location primeiro-jogo
..\ambiente\Scripts\python.exe -m mygame
```

A instalação inicial necessita de Internet para obter Pygame. Não copies a
`.venv` do computador original: o teste pretende confirmar uma instalação nova.

## Relatório a preencher

- Data:
- Windows e versão do Python (se usado):
- Nome do ZIP testado:
- Extração e arranque: passou / falhou / não testado
- Imagem e texto: passou / falhou / não testado
- Teclado, salto e pausa: passou / falhou / não testado
- Áudio: passou / falhou / não testado
- Guardar, fechar e retomar: passou / falhou / não testado
- Três níveis e vitória: passou / falhou / não testado
- Instalação do SDK e criação de jogo: passou / falhou / não testado
- Problema encontrado e passos para repetir:

Não incluas palavras-passe, tokens ou dados pessoais no relatório público.
