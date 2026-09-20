# Do motor ao jogo independente

Nesta fase, o objetivo foi provar uma separação: o motor fornece capacidades;
o jogo decide por que razão o jogador as usa.

## Primeiro: instalar, em vez de copiar

`pyproject.toml` identifica Platform2D como um pacote e declara Pygame como
dependência. A wheel contém os módulos, sons, modelos de projeto e licença.
Instalá-la num ambiente isolado permite detetar imports ou recursos que só
funcionavam por estarem ao lado da campanha de demonstração.

Experimenta gerar um projeto com `python -m platform2d new meu-jogo` e alterar
a velocidade da personagem. Essa alteração pertence ao teu jogo, não ao motor.

## Segundo: construir uma missão com componentes existentes

Em `games/resgate/resgate/scene.py`, o jogo combina `Character`, controladores,
`TileMap`, `Camera`, áudio e parallax. O primeiro setor usa plataformas, o
segundo natação e o terceiro perseguição. Não importa cenas de `examples`.

Os estados `title`, `briefing`, `pause`, `stage` e `ending` descrevem o percurso
do jogador através da aplicação. Apenas o estado de jogo ativo avança a física.
A gravação guarda progresso de missão e checkpoint; não tenta preservar cada
velocidade, gota de oxigénio ou instante da perseguição.

Experimenta alterar uma recolha ou um obstáculo no JSON e testar o percurso.
O identificador de compatibilidade da gravação depende dos mapas: uma partida
antiga é rejeitada quando as regras da missão mudam, em vez de ser carregada
num cenário incoerente.

## Terceiro: separar recursos de dados do utilizador

Os mapas e ícones pertencem ao pacote instalado. As gravações e preferências
pertencem à pasta de dados do utilizador. Essa separação permite instalar o jogo
num local onde não é permitido escrever e atualizar a aplicação sem apagar partidas.

## Quarto: verificar o produto que vai ser entregue

O teste de percurso está dentro do pacote do jogo, pelo que pode ser executado
também pelo `.exe`. Verifica a conclusão dos três níveis e a recuperação das
gravações. Os testes unitários verificam pausa, validação, confirmação de nova
partida e falhas de escrita. As capturas permitem verificar o aspeto dos menus.

A entrega separa o SDK destinado a programadores do ZIP destinado a jogadores.
Não é preciso instalar ferramentas de desenvolvimento para jogar, nem é preciso
copiar o motor para dentro de cada novo jogo.
