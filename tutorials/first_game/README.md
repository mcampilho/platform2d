# O meu primeiro jogo com Platform2D

Este projeto usa Python, Pygame e o motor com o extra `i18n` para árabe. Não importa a
campanha Aurora. O tutorial completo está em `docs/first-game-tutorial.md` na
raiz do repositório.

Com o motor instalado, nesta pasta:

```powershell
python main.py --lesson 1
python main.py --lesson 2
python main.py --lesson 3
python main.py --lesson 4
python main.py --lesson 5
python main.py --lesson 6
python main.py --language ja
```

`scene.py` contém seis camadas cumulativas, controladas por `lesson`. O motor
fornece movimento e colisões; o jogo define recolhas, adversário, vida e menus.
`python main.py --verify` verifica a conclusão através de input real.

F4 muda o idioma e guarda a preferência. Na raiz do repositório, instala com
`python -m pip install -e ".[i18n]"`. Copia também `locales/` e `fonts/` quando
separares o tutorial do repositório. O guia está em `docs/internationalization.md`.
As fontes Noto usam a licença OFL incluída em `fonts`, não a licença MIT.

Para criar um executável Windows: instala `pyinstaller==6.22.0`, executa
`python build_windows.py` e distribui toda a pasta `dist/OPrimeiroJogo`, com as
licenças relevantes. O guia de distribuição do projeto explica esses ficheiros.
Os recursos gráficos são desenhados pelo próprio código e usam a licença MIT.
