# Expedição Aurora — salas e missões variadas

**Jogar-Expedicao.cmd** abre **Expedição Aurora**, uma campanha de quatro salas com percursos, cores e objetivos diferentes.

| Sala | Tipo | Objetivo e percurso |
|---|---|---|
| Bastião de Entrada | Combate | Destruir três alvos, transpor duas coberturas de alturas diferentes e chegar à saída. |
| Jardins Suspensos | Recolha | Apanhar quatro cristais numa sequência de plataformas que sobe e volta a descer. Sem disparos. |
| Conduta Glacial | Travessia e recolha | Saltar sobre duas zonas perigosas e recolher três cristais, incluindo dois durante os saltos. Sem disparos. |
| Laboratório do Reator | Mista | Destruir dois alvos e recolher três cristais em plataformas a diferentes alturas. |

O ambiente glacial é visual: não acrescenta escorregamento ao movimento. A personagem mantém a física já conhecida. As plataformas suspensas podem ser atravessadas por baixo.

## Missões e inventário

Os diamantes dourados são **cristais de missão**. Todos os cristais e todos os alvos presentes num mapa são obrigatórios para abrir a saída. O painel indica o objetivo e as contagens; a saída fica bloqueada enquanto faltar algum deles.

Os cristais não ocupam espaço no inventário. Mesmo com kits e melhorias no limite, podes apanhá-los. As caixas D/C/+ continuam a ser melhorias e consumíveis opcionais. Os disparos ficam desativados nas salas de recolha, mas as melhorias transitam para a sala seguinte normalmente.

Morrer ou usar R conserva cristais recolhidos e alvos destruídos. Reiniciar a campanha limpa-os. F6, F9, gravações automáticas, menus e opções mantêm as regras da [fase 15](campaign-experience.md), incluindo retoma no checkpoint com vida reposta.

## Campanha anterior e gravações

**Jogar-Campanha-Classica.cmd** abre a campanha anterior, Operação Aurora, com os seus três mapas originais. Esses mapas e o respetivo manifesto foram conservados. Como cada manifesto tem o seu próprio caminho de gravação, a nova expedição não substitui o progresso da campanha anterior.

A primeira abertura da nova campanha começa sem gravação própria. As preferências de comandos continuam a ser partilhadas pelo perfil Campanha. Se usavas um caminho personalizado com `--save`, indica esse mesmo caminho ao abrir a campanha clássica.

## Editar salas e criar tipos de missão

Os quatro mapas continuam no perfil **Combate** do Atelier. O nome do perfil identifica as capacidades disponíveis; um mapa pode usá-las para combate, recolha ou ambos.

```powershell
.\Editor.cmd --map "examples\campaign\assets\expedition-2.json"
```

- **C — Cristal** coloca um cristal obrigatório.
- **5 — Alvo** e **T — Torreta** colocam objetivos de combate.
- **I — Recolhível** coloca melhorias opcionais.
- **Missão / ambiente…** escolhe Estação, Jardins, Glacial ou Reator e ativa/desativa os disparos.

Não é permitido desativar disparos enquanto existirem alvos, nem colocar alvos numa sala desarmada. Ativa primeiro os disparos para transformar uma sala de recolha numa missão mista. As alterações suportam desfazer/refazer e gravação. Usa Guardar como para criar as tuas próprias variantes.

Os dados adicionais são simples:

```json
"properties": {"theme": "garden", "weapon_enabled": false}
```

Um cristal usa `type: "coin"` e um ID único. Não há uma lista duplicada de objetivos: a missão é calculada a partir dos objetos existentes. Mapas antigos, sem estas propriedades, mantêm o ambiente Estação e os disparos ativos.

O editor valida a estrutura e os objetos bloqueados, mas não demonstra automaticamente uma solução completa neste perfil. Testa em F5 e depois na campanha, com as melhorias transportadas.

## Aprender com esta alteração

Segue [mission.py](../platform2d/gameplay/mission.py): `objectives_complete()` é a regra partilhada pelo jogo e pelo validador das gravações. Isto evita que o jogo exija cristais, mas o carregamento aceite uma vitória sem eles.

Em [scene.py](../examples/ranged/scene.py), a recolha de cristais acrescenta o ID a `collected_items`, sem chamar `Inventory.add()`. A distinção permite conservar o progresso da missão sem o ligar aos limites dos consumíveis. As partículas da aplicação reconhecem os novos IDs automaticamente.

O [gerador dos mapas](../tools/build_varied_campaign.py) mostra como combinar os mesmos objetos e controlador em percursos diferentes. Executá-lo substitui apenas os quatro mapas incluídos da expedição e o seu manifesto; guarda experiências pessoais noutros ficheiros.

`tools/check_varied_campaign.py` conclui as quatro salas sem teletransportar o jogador e sem mortes, verifica zero disparos nas duas salas desarmadas e faz uma gravação/retoma de cada resumo de vitória. Os testes também verificam a retoma com cristais parcialmente recolhidos, a missão mista e a recolha com inventário cheio.


Desde a fase 17, Jogar-Campanha.cmd abre [Odisseia Aurora](odyssey.md), que inclui estas quatro salas entre a oficina do foguetão e os novos percursos com scroll.
