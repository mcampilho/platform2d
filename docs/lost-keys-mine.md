# Mina das Chaves Perdidas

O 13.º nível da campanha adapta uma grelha compacta de **32×16 blocos**, com tiles de 32 unidades. A personagem começa no canto inferior esquerdo e precisa de recolher cinco chaves antes de entrar na saída inferior direita.

Os blocos `P` são paredes sólidas (`#`). Os blocos `C` são plataformas atravessáveis (`=`): Willy passa por elas lateralmente ou durante a subida e pousa quando cai sobre a face superior. O salto fixo atinge aproximadamente dois blocos de altura.

O modo de aventura `willy` acrescenta três objetos editáveis:

- `crumble`: sustenta a personagem durante 0,48 segundos e depois desaparece; regressa após uma morte;
- `conveyor`: funciona como plataforma e desloca a personagem na direção e velocidade configuradas;
- `patrol`: percorre apenas o intervalo `left`–`right` e provoca morte por contacto.

Os arbustos e as estalactites usam o objeto `hazard` com os estilos `bush` e `stalactite`. As chaves usam o contrato de `coin`, pelo que a saída permanece bloqueada até todas serem recolhidas e a gravação da campanha conserva a recolha.

## Arte e animação

`willy-mine.theme.json` associa o panorama pintado e três atlas ao nível. O
guardião tem oito fases de passada, âncora nos pés e inversão automática ao
mudar de direção. Os arbustos usam oito fases de balanço dessincronizadas pela
posição; as chaves conservam um halo suave e recebem um reflexo periódico.

Estas animações usam `platform2d.rendering.sprite_animation.SpriteAtlas`, a
mesma API disponível para jogos criados com a framework. A ferramenta abaixo
valida as células e os clips e gera uma folha com o fundo, a paleta e os sprites:

```powershell
python -m platform2d theme check examples\campaign\assets\willy-mine.theme.json --preview artifacts\willy-theme-preview.png
```

## Jogar apenas este nível

Executa **`Jogar-Mina-Chaves.cmd`** na raiz do projeto. O atalho abre uma campanha independente com apenas a Mina e usa uma gravação separada da campanha principal. Pela linha de comandos, o equivalente é:

```powershell
python -m examples.campaign --campaign "examples/campaign/assets/willy.json"
```

O Atelier mostra ferramentas próprias quando o mapa usa `"traversal": "willy"`. Como os pisos mudam durante a partida e existe um inimigo móvel, a análise automática assinala a validação dinâmica como inconclusiva e recomenda o teste F5. A validação estrutural confirma dimensões, objetos, limites da patrulha, saída, chaves e zonas letais.

## Solução verificada

O projeto inclui uma sequência determinística em `examples/campaign/willy_solution.py`. Ela executa a física real a 60 atualizações por segundo, recolhe as cinco chaves, atravessa os pisos quebradiços, evita todos os perigos e entra na saída sem morrer. As duas chaves que estavam na linha superior do esboço foram descidas para a altura alcançável pelo salto de dois blocos.

Para voltar a verificar a solução após editar o mapa ou o movimento:

```powershell
python -m examples.campaign.willy_solution
```

Qualquer alteração que invalide a rota faz também falhar o teste automático da Mina.
