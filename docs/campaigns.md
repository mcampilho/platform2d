# Campanhas — fase 14

Abre **Jogar-Campanha-Classica.cmd** para jogar **Operação Aurora**, uma sequência de três arenas de Combate: Armazém de Abastecimento, Posto de Segurança e Núcleo de Comando. A disposição da cobertura mantém-se para poderes comparar o efeito das melhorias: os alvos ganham resistência e as torretas disparam mais depressa nos níveis seguintes. Desde a fase 15, começa no menu inicial e inclui gravação, pausa e opções: consulta [a experiência de campanha](campaign-experience.md).

## Jogar

- Movimento, salto, K/X para disparar e H para usar kits mantêm-se.
- Destrói todos os alvos e chega à saída. O resumo mostra os totais acumulados e o próximo nível.
- **Enter** avança após a vitória; no gamepad, **RB**. F3 permite configurar estes comandos no perfil próprio **Campanha**.
- As melhorias e os kits transitam para o próximo nível; a vida é reposta. Os limites do inventário continuam a aplicar-se.
- **R** restaura o checkpoint do nível atual e conserva as melhorias. No resumo de vitória, R não tem efeito.
- **F2** pede confirmação para reiniciar a campanha inteira, incluindo inventário e estatísticas. No último nível surge o resumo final.

A passagem requer uma nova pressão depois de terminar o nível. Manter Enter premido durante o jogo não salta o resumo. Pausa e F3 suspendem a simulação; o tempo apresentado contabiliza apenas os passos de jogo, excluindo os resumos.

## Criar a tua campanha

O ficheiro [campaign.json](../examples/campaign/assets/campaign.json) lista os mapas pela ordem de jogo:

```json
{
  "format": "platform2d.campaign",
  "version": 1,
  "name": "A minha campanha",
  "stages": [
    {"id": "entrada", "map": "entrada.json"},
    {"id": "final", "map": "final.json"}
  ]
}
```

Os caminhos relativos são resolvidos a partir da pasta deste ficheiro. Cada nível precisa de um ID diferente. Os IDs dos objetos podem repetir-se em mapas diferentes: uma caixa recolhida no primeiro mapa não apaga uma caixa com o mesmo ID no segundo.

1. Cria mapas do perfil Combate no Atelier e guarda-os numa pasta própria. Podes usar Editor-Inventario.cmd como ponto de partida.
2. Escreve um ficheiro de campanha nessa pasta, com os caminhos e a ordem pretendidos.
3. Inicia com:

```powershell
.\Jogar-Campanha.cmd --campaign "levels\minha-campanha\campaign.json"
```

Para estudar um dos mapas incluídos:

```powershell
.\Editor.cmd --map "examples\campaign\assets\stage-2.json"
```

Usa **Guardar como** para criar a tua cópia. F5 testa apenas esse mapa, com inventário inicial vazio; para verificar as melhorias transportadas, joga a campanha. Desde a fase 19, **Editor-Campanhas.cmd** permite escolher e ordenar os níveis visualmente. Consulta [o editor de campanhas](campaign-editor.md).

Todos os mapas são carregados e validados antes de começar. São aceites entre 1 e 32 níveis dos perfis Combate e Aventura. Um mapa em falta, perfil incorreto ou erro estrutural interrompe a abertura com uma mensagem. Os avisos de validação continuam a exigir teste manual: não existe pesquisa automática de uma solução de combate.

## Regras da passagem

Cada nível usa os seus próprios parâmetros de arma como base. As melhorias acumuladas são aplicadas a essa base. Checkpoints, inimigos, caixas recolhidas e projéteis pertencem ao nível atual; o seguinte começa com estado novo. Vida completa na entrada de cada nível é uma regra desta demonstração, não uma obrigação do motor.

A campanha é linear. Desde a fase 15, podes guardar com F6 e retomar através de Continuar gravação; existem também gravações automáticas nos checkpoints e nas mudanças de nível. Não há seleção livre de níveis, caminhos alternativos. As funcionalidades de gravação dos exemplos Salas continuam independentes. Consulta [as regras de retoma e compatibilidade](campaign-experience.md).

## Verificar

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_campaign.py
.venv\Scripts\python.exe tools\check_campaign_route.py
```

O percurso automático envia eventos de teclado, conclui os três níveis sem teletransportar o jogador, confirma a passagem do inventário e verifica que os documentos não mudaram. Guarda uma captura do resumo de cada nível em `artifacts/campaign-stage-1.png` a `campaign-stage-3.png`.


Desde a fase 18, Jogar-Campanha.cmd abre a Odisseia Aurora com oito etapas, terminando no [Pátio do Guardião](sword-and-defence.md). Jogar-Odisseia.cmd conserva as sete etapas da fase 17. Jogar-Expedicao.cmd conserva a [Expedição Aurora](varied-campaign.md), com quatro salas. A campanha descrita acima continua disponível no atalho clássico.
