# Fase 19 — editor visual de campanhas

Abre **Editor-Campanhas.cmd**. O Atelier apresenta uma cópia por guardar da campanha atual, com oito etapas. Podes organizar a sequência sem editar JSON. **Nova** começa uma campanha vazia; **Abrir** permite navegar por pastas e escolher uma campanha existente.

O editor de mapas também oferece **Novo → Campanha**. Ao abrir um manifesto pelo botão Abrir, reconhece-o e entra no espaço de campanhas. **F4** regressa ao mapa de origem.

## Organizar a sequência

1. Usa **Adicionar mapa**. Escolhe um ficheiro de mapa dos perfis Combate ou Aventura. A janela permite percorrer pastas, subir à pasta anterior ou escrever um caminho.
2. Seleciona uma etapa na lista. Vês o nome, o ID, o perfil, o caminho e uma miniatura do mapa.
3. Usa **Subir/Descer** ou **Shift+↑/↓** para reordenar. **Começar aqui** move a etapa selecionada para o início, conservando as restantes na sua ordem relativa.
4. **Mudar nome** altera o título da campanha. **Mudar ID** altera o identificador da etapa; os IDs têm de ser únicos.
5. **Trocar mapa** substitui a referência da etapa. **Retirar etapa** remove só essa referência; não apaga ficheiros.

Podes usar o mesmo mapa em várias etapas; o editor gera IDs diferentes. A campanha aceita entre 1 e 32 etapas. Uma campanha vazia pode ser preparada no editor, mas precisa de pelo menos um mapa válido para ser guardada ou testada.

**Desfazer/Refazer**, **Ctrl+Z/Ctrl+Y** e **Ctrl+Shift+Z** cobrem nome, IDs, referências, remoções e ordem. A primeira etapa da lista é sempre o início da campanha. Não há ramos ou etapas anteriores escondidas por uma seleção de início.

## Testar

- **F5 — Testar tudo:** começa na primeira etapa.
- **F6 — Testar daqui:** começa na etapa selecionada e segue até ao fim. Não altera a ordem guardada. O inventário começa vazio.
- **Enter:** passa à etapa seguinte depois de vencer, conservando as melhorias e os kits obtidos durante esse teste.
- **P:** pausa; **F3:** configura os comandos do teste.
- **F5 ou Esc:** termina o teste e volta ao editor.

O teste usa as mesmas cenas da aplicação Campanha. Não cria nem altera gravações de progresso; os comandos F6/F9 de guardar/carregar não estão disponíveis durante este teste. O estado jogado é descartado ao regressar. As preferências de comandos deste painel também estão separadas das preferências da campanha normal.

## Validar e corrigir

**F8** relê os mapas e mostra os erros e avisos de cada etapa. Clica num resultado para ler o detalhe completo. São verificados ficheiros em falta, formato, perfis, IDs repetidos, estrutura dos mapas e as validações já existentes de cada perfil.

Uma campanha com uma referência em falta pode ser aberta para reparação: seleciona a etapa e usa **Trocar mapa**. Erros impedem guardar e testar. Avisos permitem continuar, mas exigem verificação manual. A validação não garante automaticamente que todos os percursos ou combates têm solução.

**Editar mapa** abre o editor habitual para a etapa selecionada. **F4** regressa à campanha, perguntando o que fazer se houver alterações por guardar. A lista volta a ler o mapa e atualiza o nome e a validação. O histórico do mapa é independente do histórico da campanha.

Editar e guardar um mapa altera o ficheiro referenciado, incluindo outras campanhas que o utilizem. Para criar uma variante, usa **Guardar como** no editor do mapa; ao voltar, usa **Trocar mapa** para apontar a etapa para a cópia.

## Guardar e jogar fora do editor

**Ctrl+S** guarda a campanha; **Guardar como** permite escolher outro ficheiro. O atalho propõe `levels/minha-campanha.json`.

Guardar como exporta o manifesto, mantendo referências aos mesmos mapas. Os caminhos são recalculados em relação à nova pasta, para continuarem a funcionar. Não copia os mapas nem os recursos. Se moveres o projeto para outro computador, conserva também os ficheiros referenciados e a sua organização de pastas. Referências entre unidades Windows diferentes precisam de caminhos absolutos.

Para jogar a tua campanha na aplicação habitual, com menus e gravações:

```powershell
.\Jogar-Campanha.cmd --campaign "levels\minha-campanha.json"
```

Uma campanha guardada noutro caminho recebe uma gravação de progresso independente. Alterar IDs, ordem ou mapas pode tornar uma gravação anterior incompatível; as verificações existentes impedem carregá-la sobre uma campanha diferente. As campanhas fornecidas continuam disponíveis nos mesmos atalhos.

## Verificação desta entrega

`tools/check_campaign_editor.py` escolhe mapas pela interface, reordena e desfaz, guarda noutra pasta, reabre e termina duas etapas através de eventos de teclado. Verifica a passagem do inventário e a preservação dos mapas. Os testes em `tests/test_campaign_editor.py` cobrem referências em falta, IDs, limite de etapas, histórico, escrita atómica, erro de gravação e edição de mapas dentro da campanha.


Desde a fase 20, podes usar **Editar mapa → F8** para procurar e reproduzir uma solução de Aventura sem combate. A validação da lista de campanha continua estrutural. Consulta [validar percursos](adventure-validation.md).


O atalho abre uma cópia da campanha de 13 etapas, incluindo [Novos Horizontes](new-horizons.md) e a [Mina das Chaves Perdidas](lost-keys-mine.md). O manifesto `odyssey-duel.json` conserva as oito etapas anteriores.
