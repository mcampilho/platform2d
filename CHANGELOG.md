# Histórico de versões

## 0.24.0 — direção visual, internacionalização e campanha expandida

- Temas visuais JSON validados, com paleta herdável, imagens e fatores de parallax.
- Tema básico sem recursos obrigatórios e tema Observatório aplicado ao Mundo Vivo.
- Atelier com ambiente Observatório e demonstração na campanha, no Vale das Três Luas.
- Terreno, objetos interativos, personagem, efeitos e interface com direção visual coerente.
- Guia para criar, validar e distribuir temas próprios.
- Gravações de campanha deixam de ser invalidadas por mudanças apenas visuais; ficheiros anteriores ao tema Observatório são migrados na gravação seguinte.
- `python -m platform2d theme new/check` cria um tema modelo, valida as imagens e gera uma folha de pré-visualização.
- Os projetos criados por `platform2d new` incluem um tema editável, usam a paleta na cena inicial e empacotam o manifesto automaticamente.
- F7 recarrega temas no projeto modelo e no Mundo Vivo; erros conservam o último conjunto visual válido e são mostrados sem interromper a partida.
- Câmara configurável com antecipação de velocidade e impulsos visuais determinísticos, opcionais e separados da física.
- Transições reutilizáveis para entrada, checkpoint e conclusão, integradas na campanha e na opção de efeitos reduzidos.
- Indicadores de margem para objetivos fora do ecrã nos níveis com scroll, sem revelar mecanismos de puzzles.
- 13.º nível, Mina das Chaves Perdidas: grelha 32×16, cinco chaves, pisos quebradiços, transportador, patrulha e perigos clássicos.
- A Mina distingue paredes sólidas de pisos atravessáveis, usa salto fixo de dois blocos e possui um atalho para jogar isoladamente.
- A solução da Mina é reproduzida na física real: cinco chaves e saída, sem mortes; duas chaves superiores foram colocadas ao alcance do salto.
- Atlas de sprites reutilizáveis com clips, velocidade, repetição, âncoras e inversão direcional.
- Temas podem declarar sprites animados; a verificação valida os atlas e inclui-os na folha de pré-visualização.
- Guardião, vegetação e chaves da Mina usam recursos pintados, animação pré-calculada e contacto visual com o terreno.

- Campanha Aurora e editores com seleção entre oito idiomas.
- Nomes dos níveis, menus, ferramentas e diagnósticos frequentes traduzidos; verificação visual de 12 níveis e 14 perfis de editor.
- Resgate completo em oito idiomas, com catálogos externos e fontes instaláveis.
- Painel comum e áudio traduzidos; colunas RTL, mensagens de validação e ajuda com teclas reais.
- Verificação de todos os setores e menus, cobertura de caracteres e gravações entre idiomas.
- O código mantém MIT; as fontes Noto incluídas usam OFL-1.1.

- Tutorial em pt-PT, en, es, fr, de, zh-Hans, ar e ja; F4 muda e guarda o idioma.
- Catálogos UTF-8 por jogo, validação de parâmetros e texto de reserva.
- Fontes Noto no tutorial, árabe bidirecional e alinhamento à direita.
- Verificação dos oito idiomas no CI.
- `Game`/`ControlsPanel` aceitam um idioma para os rótulos dos comandos.
- Distribuições 0.24.0 preparadas para validação local, TestPyPI e PyPI.

## 0.23.0 — primeira distribuição pública preparada

- Licença MIT e pacote Python instalável com recursos incluídos.
- `python -m platform2d new` cria um projeto independente; `doctor` mostra a instalação.
- Diretório de dados por aplicação, separado dos recursos instalados.
- Resgate na Estação 1.0.0: três setores, menus, gravação e distribuição Windows x64.
- Tutorial progressivo, guias GitHub/PyPI, modelos de issues e testes automáticos.
- Wheel e distribuição de código-fonte validadas antes da publicação.

Esta versão está preparada localmente. Este ficheiro não afirma que já foi
publicada no GitHub, TestPyPI ou PyPI.

## 0.22.0

Novos Horizontes: caixas e peso, natação e oxigénio, fuga e exploração com salto
duplo adquirido. Campanha com 12 níveis.

## 0.21.0

Poses e efeitos de transporte, espada, defesa, dano e recuperação.

## 0.20.0

Pesquisa limitada e reprodução de soluções de aventura, sem combate.

As fases anteriores e os respetivos guias estão descritos em `docs/project-history.md`.
