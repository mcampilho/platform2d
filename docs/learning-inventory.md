# Aprender com a fase 13: da caixa no mapa ao efeito no jogador

Começa por recolher a primeira caixa roxa em **Arsenal de Campo**. O painel passa de dano 1 para dano 2. Para compreender esta mudança, acompanha três representações diferentes do mesmo acontecimento.

## 1. O mapa descreve uma caixa

Em [inventory_level.py](../examples/ranged/inventory_level.py), cada objeto tem posição, tamanho, ID, tipo de item e quantidade. Estes dados descrevem o que pode ser recolhido. Não dizem quantos itens o jogador já possui.

O modelo aproveita a definição de Linha de Defesa e acrescenta quatro caixas. Não foi preciso copiar a física, os disparos ou o comportamento das torretas. É um exemplo de criar uma variante através dos dados.

**Experiência:** abre Editor-Inventario.cmd, muda a primeira caixa para Cadência e testa. O intervalo muda, mas o dano mantém-se. Guarda a experiência num mapa próprio.

## 2. O inventário guarda apenas quantidades

Abre [inventory.py](../platform2d/gameplay/inventory.py). `ItemDefinition` define um tipo de item e o limite. `Inventory` guarda as quantidades atuais e oferece quatro operações pequenas:

```python
inventory = Inventory()
inventory.add("medkit", 2)   # True: guardou dois
inventory.add("medkit", 2)   # False: ultrapassaria o limite de três
inventory.take("medkit")     # True: consumiu um
inventory.count("medkit")    # 1
```

Uma operação recusada deixa o estado igual. Isto evita perder metade de uma caixa ou consumir um item inexistente. `snapshot()` devolve uma cópia: alterar o resultado não altera o inventário original.

Repara que esta classe não importa Pygame e não conhece posições, teclas ou imagens. Pode ser usada noutro jogo com um catálogo diferente, por exemplo `Inventory([ItemDefinition("key", "Chave", 5)])`. Os efeitos das melhorias desta demonstração continuam a usar o catálogo Potência/Cadência/Kit.

**Experiência:** no editor, coloca uma caixa de dois kits após outra de dois. Recolhe a primeira e observa a recusa da segunda. Recebe dano, usa um kit e volta à segunda caixa: agora cabem os dois.

## 3. A cena liga o contacto à recolha

Em [scene.py](../examples/ranged/scene.py), `collect_items()` verifica a sobreposição entre personagem e caixa. Pede ao inventário para adicionar a quantidade. Só se a operação resultar é que guarda o ID da caixa em `collected_items`.

Este conjunto impede recolhas repetidas. A caixa permanece na definição do mapa; o desenho consulta o conjunto para saber se deve mostrá-la. Assim, reiniciar a partida exige limpar o estado da sessão, sem reconstruir ou reescrever o mapa.

**Experiência:** apanha uma melhoria e prime R. Manténs a melhoria e a caixa continua ausente. Prime F2: o conjunto e o inventário são limpos, a caixa reaparece e a arma volta ao início. Compara `respawn()` e `reset()` para perceber esta diferença.

## 4. Os efeitos são calculados a partir da arma original

`upgraded_weapon(base, inventory)` cria uma nova especificação:

```python
dano = min(100, base.damage + inventory.count("power"))
intervalo = max(.02, base.cooldown * .8 ** inventory.count("rapid"))
```

A base é sempre a especificação original, não a que já foi melhorada. Com uma melhoria, o intervalo é 0,24 × 0,8 = 0,192 s. Voltar a calcular com o mesmo inventário produz o mesmo resultado. Se multiplicássemos repetidamente o valor já alterado, recolher um kit poderia acelerar a arma por engano.

`WeaponSpec` é imutável. A arma passa a referir uma nova especificação, enquanto os projéteis existentes continuam com a antiga. A mudança de equipamento não altera retroativamente tiros já disparados.

## 5. Um consumível exige uma intenção e uma condição

O kit usa `actions.pressed`, não `actions.held`: uma pressão pede um uso. A cena verifica que a personagem está viva, tem vida em falta e possui um kit. Só então consome o item e chama `Health.heal(2)`.

`heal()` limita a vida ao máximo e não ressuscita. Também mantém o período de invulnerabilidade existente, sem o prolongar. No passo do jogo, impactos e morte são resolvidos antes dos itens; uma caixa não salva automaticamente uma personagem que já morreu nesse passo.

O pedido de uso acontece antes da recolha. Se tocares numa caixa e premires H no mesmo passo sem teres kits, recolhes o kit e podes usá-lo numa nova pressão.

## 6. Seguir o comportamento nos testes

Lê [test_inventory.py](../tests/test_inventory.py) por esta ordem: capacidade indivisível, recolha única, vida completa, tiros antigos e reinício. Estes casos descrevem regras observáveis, não apenas nomes de funções.

Depois executa:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_inventory.py
.venv\Scripts\python.exe tools\check_inventory_route.py
```

O primeiro comando verifica situações isoladas; o segundo atravessa editor, ficheiro, input e partida completa. Esta combinação ajuda a descobrir tanto erros nas regras como falhas na ligação entre os sistemas.
