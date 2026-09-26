# O meu primeiro jogo com Platform2D

O objetivo é compreender cada responsabilidade antes de acrescentar a seguinte.
As seis lições são executáveis e cumulativas; a última é um pequeno jogo completo.
O tutorial tem oito idiomas: **F4** muda de idioma. Consulta o
[guia de internacionalização](internationalization.md) para traduzir os textos.

## Preparação

Instala Python 3.12, extrai o código do projeto e abre o terminal na sua raiz:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[i18n]"
.venv\Scripts\python.exe tutorials/first_game/main.py --lesson 1
```

Para esta fase multilingue, usa o código atual do repositório: o SDK 0.24.0
anterior ainda não a inclui. O tutorial não precisa dos exemplos da Aurora.

## Lição 1 — abrir uma janela

Abre `tutorials/first_game/main.py`. A criação de `Game` fornece uma cena e as
teclas; o método `run` processa eventos, atualiza e desenha. A cena tem dois métodos:

```python
def update(self, dt, actions):
    pass  # Avançar o estado do jogo.

def draw(self, surface, alpha):
    surface.fill((12, 23, 37))
```

Na primeira lição, a janela mostra apenas texto. Experimenta outra cor de fundo
em `scene.py` e volta a executar. Fechar a janela termina o jogo.

## Lição 2 — personagem, chão e input

Executa o mesmo comando com `--lesson 2`. Um `Body` guarda posição e velocidade;
`Character` combina o corpo com o controlador de movimento. `Collider(Box(...))`
descreve o chão. A cena chama `player.update(dt, actions, floor)`.

O motor traduz teclas em ações como `left`, `right` e `jump`. Por isso, mudar
a tecla em F3 não exige alterar a lógica de movimento. Experimenta deslocar o
ponto inicial de `(80, 482)` para `(160, 482)`.

## Lição 3 — plataformas e salto

Com `--lesson 3`, aparece uma plataforma a Y=448. O seu `Collider` tem
`one_way=True`: permite saltar através dela por baixo e aterrar por cima.
Y aumenta para baixo no ecrã; subir uma plataforma significa diminuir Y.

Move a plataforma para Y=416 e observa a diferença. Não alteres a posição
da personagem durante o desenho: usa `body.interpolated(alpha)` para obter
uma posição visual suave entre passos de simulação.

## Lição 4 — uma regra de missão

Com `--lesson 4`, recolhe a esfera na plataforma e chega à porta à direita.
`Box.overlaps` verifica contacto; `collected` regista a recolha; `won` impede
a simulação de continuar após a vitória.

A física não sabe o que é uma esfera nem uma vitória. Estas são regras do jogo.
Experimenta colocar a esfera noutro local e confirmar que a saída continua
bloqueada enquanto não a apanhares.

## Lição 5 — adversário e vida

Com `--lesson 5`, um adversário patrulha entre X=620 e X=748. O contacto reduz
a vida e repõe a personagem no início. `Health` impede que um contacto prolongado
aplique dano em todos os passos. Ao perder toda a vida, o nível recomeça.

Salta por cima dele. Experimenta mudar a velocidade de 70 para 90. A patrulha
simples serve para aprender; para comportamentos mais elaborados, consulta
os módulos de perceção e estados do motor.

## Lição 6 — início, pausa e final

Com `--lesson 6`, prime Enter para começar. P pausa; R recomeça. A simulação
só avança durante a partida ativa. Na pausa e no final, as posições anteriores
são alinhadas com as atuais para evitar oscilações visuais.

Experimenta alterar as mensagens de início e vitória. Depois verifica o jogo:

```powershell
.venv\Scripts\python.exe tutorials/first_game/main.py --verify
```

O teste joga realmente: sobe à plataforma, recolhe a esfera, evita o inimigo e
alcança a porta sem dano. Um percurso verificado não prova que todas as alterações
futuras são possíveis; repete o teste e experimenta manualmente quando mudares o mapa.

## Criar um executável

No mesmo ambiente, instala o PyInstaller e executa a receita:

```powershell
.venv\Scripts\python.exe -m pip install pyinstaller==6.22.0
.venv\Scripts\python.exe tutorials/first_game/build_windows.py
```

O resultado está em `tutorials/first_game/dist/OPrimeiroJogo`. Abre
`OPrimeiroJogo.exe` e conserva a pasta `_internal`. Ao partilhar, inclui as
licenças do motor e dependências, como no Resgate. Consulta o
[guia de distribuição](distributing-platform2d.md).

Depois deste tutorial, usa `python -m platform2d new outro-jogo` para começar
um projeto teu ou estuda `games/resgate`, que acrescenta mapas em JSON,
três setores e gravação em disco.
