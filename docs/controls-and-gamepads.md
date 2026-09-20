# Comandos configuráveis e gamepad — versão 0.10.0

Abre qualquer jogo pelos atalhos habituais e prime **F3**. No Atelier, entra primeiro no teste com **F5** e depois usa **F3**. O painel suspende a simulação e o áudio; fechá-lo conserva o estado anterior de pausa.

## Alterar comandos

1. Clica na célula de uma tecla ou botão. Também podes selecionar com as setas/Tab e premir Enter.
2. Prime a nova tecla ou um botão do gamepad ativo. Escape cancela a captura.
3. Escolhe **Guardar**, ou usa Ctrl+S, para aplicar e guardar. Cancelar, Escape ou F3 fecha o painel sem aplicar o rascunho.

Cada ação mantém uma tecla principal obrigatória e pode ter uma alternativa. Delete/Backspace limpa a alternativa ou o botão selecionado. As teclas repetidas entre ações e os botões repetidos são rejeitados, incluindo quando a repetição usa outro nome para a mesma tecla. Para trocar duas atribuições ocupadas, usa temporariamente uma tecla livre; nos botões podes primeiro limpar a atribuição anterior.

**Repor origem** prepara os comandos originais; só os aplica quando escolhes Guardar. As teclas Escape, F3, F5 e F10–F12 ficam reservadas à aplicação. Os atalhos de edição de mapas não são remapeados. A reprodução automática de uma solução continua a usar as ações calculadas pelo verificador e não abre este painel.

Os avisos de interação, pausa e vitória e a barra inferior acompanham os comandos configurados. Os textos decorativos dos mapas podem ainda referir as teclas de origem; F3 mostra a configuração completa em vigor.

## Gamepad

São aceites comandos reconhecidos pela interface SDL GameController incluída no Pygame. Esta interface normaliza os botões segundo as posições Xbox, mesmo em comandos com outros símbolos. A deteção utiliza a [interface oficial de controllers do Pygame](https://www.pygame.org/docs/ref/sdl2_controller.html).

| Comando de origem | Ação, quando existe no jogo |
|---|---|
| Direcional / analógico esquerdo | Mover, subir ou descer |
| A (botão inferior) | Saltar |
| B (botão direito) | Dash |
| X (botão esquerdo) | Atacar |
| Y (botão superior) | Interagir / continuar diálogo |
| Start | Pausa |
| Back | Voltar ao checkpoint |
| LB / RB | Guardar / carregar progresso no perfil Salas |

Os botões podem ser alterados no painel. O direcional e o analógico esquerdo ficam dedicados ao movimento. A zona morta é ajustável de 20% a 70%, com valor inicial de 35%. Abaixo desse limiar pequenos desvios não iniciam movimento; o limiar para parar é dez pontos percentuais inferior para evitar oscilações. O movimento é digital, com a mesma velocidade do teclado; o analógico permite diagonais para o dash.

Podes ligar ou desligar o comando durante o jogo. O primeiro comando reconhecido fica ativo; se for desligado, outro comando já ligado assume o controlo. O teclado continua disponível em simultâneo. Ao desligar o gamepad, as suas ações são libertadas sem retirar ações ainda mantidas pelo teclado. Após perder o foco, centra o analógico antes de voltar a deslocá-lo. Ao sair do painel, larga as teclas e os botões que usaste antes de voltar a jogar.

O painel é operado com teclado/rato; o gamepad serve para jogar e para capturar botões. Não há navegação do painel por gamepad, vibração, gatilhos remapeáveis, analógico direito ou suporte genérico a joysticks sem mapeamento SDL nesta entrega. Recomeçar toda a sessão e os comandos de diagnóstico mantêm apenas teclado por predefinição, mas podem receber um botão livre.

## Preferências

As preferências são criadas apenas quando guardas, na pasta `preferences` do projeto, ao abrir pelos atalhos:

- `classic.controls.json`: Estação Aurora e testes Clássico.
- `rooms.controls.json`: Arquivo Lunar, Central de Energia e testes Salas/Mecanismos.
- `precision.controls.json`: Ascensão e testes Precisão.
- `sentinels.controls.json`: Sentinelas.

A gravação usa substituição atómica. Mapas, definições dos jogos e ficheiros de progresso ficam separados. Se houver uma falha ao guardar, o painel mantém-se aberto e a configuração anterior continua ativa. Ficheiros inválidos geram um aviso e os comandos de origem são usados; ficheiros irreconhecíveis ou de outra versão/perfil são preservados. Para recuperar, fecha o jogo, renomeia o ficheiro indicado acima e volta a guardar as preferências.

Podes escolher outra pasta para testes independentes:

```powershell
.venv\Scripts\python.exe -m examples.precision --controls-dir preferences-teste
.venv\Scripts\python.exe -m examples.editor --profile precision --controls-dir preferences-teste
```

## Integração e verificação

`Input` combina teclado, botões e analógico no contrato existente `Actions(held, pressed, released)`. As bordas são calculadas sobre a união das fontes: soltar uma tecla não cancela um salto ainda mantido no gamepad. `Gamepads` mantém os dispositivos por identificador de instância, processa ligação/desligação e ignora eventos de joystick duplicados. `ControlSettings` valida e guarda os perfis; `ControlsPanel` oferece a interface usada pelo anfitrião `Game` e pelo teste do editor. Uma aplicação que não pretenda persistência pode omitir o caminho das preferências.

Os testes cobrem conflitos, teclas reservadas, perda de foco, zona morta, botões simultâneos, desconexão, gravação atómica, ficheiros inválidos e isolamento do editor. `tools/check_controls_workflow.py` conclui Salas com salto remapeado no teclado e Precisão com eventos de analógico e botão remapeado, sem mortes nem alterações ao mapa. Estes eventos são simulados; não substituem um teste com um comando físico específico.


Na versão 0.12.0, Linha de Defesa e o perfil Combate acrescentam a ação `shoot`: K/X no teclado e X no gamepad por predefinição. As preferências ficam em `preferences/ranged.controls.json`.

Na versão 0.13.0, a ação `use_item` usa **H/Y** para consumir um kit médico. Preferências válidas de uma versão anterior conservam os comandos existentes; ações acrescentadas recebem teclas livres, usando F4 como primeira alternativa se H estiver ocupado. Um botão ocupado não é reatribuído: a nova ação fica sem botão até o escolheres em F3. Esta adaptação só é escrita no ficheiro ao guardar as preferências. Arsenal de Campo e Linha de Defesa partilham o perfil Combate.
