# Inventário e melhorias — fase 13

Abre **Jogar-Inventario.cmd** para jogar **Arsenal de Campo**. Usa K/X para disparar, recolhe as caixas por contacto, salta a cobertura central e destrói os quatro alvos para abrir a saída. As regras de movimento e disparo são as mesmas de Linha de Defesa.

| Símbolo | Item | Efeito | Limite |
|---|---|---|---|
| D, roxo | Potência | +1 dano por melhoria | 3 |
| C, azul | Cadência | Multiplica o intervalo entre tiros por 0,8 | 2 |
| +, verde | Kit médico | Recupera até 2 pontos de vida quando usado | 3 |

**H usa um kit**; no gamepad, o botão predefinido é **Y**. Uma pressão consome no máximo um kit. Com vida completa, o kit fica guardado. F3 permite alterar estes comandos; os rótulos do jogo acompanham as preferências. As melhorias de potência e cadência aplicam-se automaticamente.

O painel mostra as quantidades e os valores atuais da arma. Com a arma inicial, duas melhorias de potência dão dano 3; uma melhoria de cadência reduz 0,24 s para 0,192 s (apresentado como 0,19 s). O dano nunca excede 100 e o intervalo nunca desce abaixo de 0,02 s.

## Recomeçar e conservar progresso

- Morrer ou usar **R** restaura a vida no checkpoint e conserva o inventário, os recolhíveis já apanhados e os alvos destruídos. Inimigos sobreviventes recuperam a resistência.
- **F2** reinicia toda a partida: inventário vazio, arma original, recolhíveis e alvos repostos.
- Pausa e painel de comandos suspendem o jogo. O avanço de um passo durante a pausa continua disponível.
- O inventário existe apenas durante a sessão. Este perfil ainda não guarda partidas em disco.

Os tiros que já estão no ar mantêm o dano com que nasceram. Recolher uma melhoria não reinicia o tempo de espera da arma.

## Criar recolhíveis no Atelier

1. Abre **Editor-Inventario.cmd**. O modelo pertence ao perfil **Combate**; o inventário também está disponível em **Editor-Combate.cmd**.
2. Escolhe **I — Recolhível** e coloca uma caixa. Por predefinição, contém um kit.
3. Seleciona-a com V e abre **Configurar recolhível…** no painel da direita.
4. Escolhe Potência, Cadência ou Kit médico e a quantidade. Ao mudar para um tipo com limite menor, a quantidade é reduzida ao respetivo limite.
5. Usa F8 para validar e F5 para testar. Guarda o mapa; o teste não altera os seus objetos.

Desfazer/refazer inclui tipo e quantidade. O editor rejeita tipos desconhecidos, quantidades não inteiras e valores fora dos limites. Também assinala recolhíveis totalmente bloqueados por sólidos ou perigos, sobreposições parciais e objetos fora do mapa. Tal como na fase 12, a validação do perfil Combate **não demonstra uma solução completa**: combate e acessibilidade devem ser testados em F5.

A recolha de uma caixa é indivisível. Por exemplo, se tens dois kits e a caixa contém dois, não cabe no limite de três: permanece no mapa até haver espaço para ambos. A indicação de falta de espaço aparece ao entrar em contacto, sem repetir o som em todos os passos.

Exemplo de objeto JSON:

```json
{"id":"medical-a","type":"pickup","item":"medkit","quantity":1,
 "x":520,"y":482,"w":24,"h":30}
```

O ID identifica a caixa no mapa; `item` identifica o tipo no catálogo. Duas caixas de kits precisam de IDs distintos, mas partilham `item: "medkit"`.

Para abrir um mapa guardado:

```powershell
.\Jogar-Inventario.cmd --map "levels\meu-inventario.json"
```

## Compatibilidade e verificação

Mapas de Combate da fase 12 continuam válidos sem recolhíveis. Preferências de comandos válidas mantêm as teclas e os botões existentes: a nova ação recebe H/Y quando estão livres. Se H já estiver ocupado, recebe uma tecla livre (primeiro F4); se Y estiver ocupado, fica sem botão até ser configurado em F3. O ficheiro só é atualizado ao guardar as preferências.

`tools/check_inventory_route.py` configura uma caixa no editor, desfaz/refaz, guarda/reabre e conclui o nível com eventos de teclado: recolhe as melhorias, recebe dano, usa um kit e sai sem mortes. As capturas ficam em `artifacts/editor-inventory.png`, `inventory-battle.png` e `inventory-completed.png`.

O inventário reutilizável guarda contagens por tipo. Ainda não há grelha de espaços, armas equipáveis, troca de equipamento, descarte de objetos ou persistência neste perfil.
