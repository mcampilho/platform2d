# Aprender com a fase 15: três sistemas em torno do mesmo jogo

Esta entrega junta três funcionalidades, mas mantém as suas responsabilidades separadas. Segue esta ordem de leitura: **progresso → aplicação e menus → efeitos visuais**. A campanha e o combate das fases anteriores continuam no centro.

## 1. Guardar uma intenção de retoma

Em [progress.py](../examples/campaign/progress.py), `capture()` produz um dicionário de dados simples: nível, inventário, objetos recolhidos, alvos destruídos, checkpoint e estatísticas. Não tenta transformar todos os objetos Python em JSON.

O contrato escolhido é «retomar no checkpoint». Isso permite dispensar velocidades, projéteis, temporizadores de invulnerabilidade e partículas. Ao carregar, estas partes transitórias são reconstruídas com valores seguros.

**Experiência:** guarda durante um salto e continua a gravação. Reapareces no checkpoint, sem repetir o salto. É uma regra explícita, não informação esquecida por acidente.

## 2. Validar antes de alterar

`validate()` verifica todo o dicionário. Só depois `restore()` constrói uma cena candidata, preenche o inventário, calcula a arma e restaura os conjuntos de IDs. A cena ativa é substituída apenas no fim.

Esta ordem evita uma partida parcialmente carregada: por exemplo, inventário novo com nível antigo porque o checkpoint era inválido. Os testes com dados inválidos comparam o estado antes e depois da tentativa.

A identidade da campanha é um resumo calculado a partir dos seus dados. Se um mapa mudar, uma gravação antiga pode referir objetos que deixaram de existir. Rejeitar essa combinação é mais claro do que tentar adivinhar onde estavam. A identidade não é uma assinatura de segurança nem impede alguém de editar uma gravação coerente.

**Experiência numa cópia:** altera a quantidade de kits para 99 no JSON gravado. O carregamento deve recusar a quantidade e deixar a partida atual intacta.

## 3. Separar o formato da escrita em disco

[json_slot.py](../platform2d/gameplay/json_slot.py) não conhece personagens. Recebe uma função de validação e encarrega-se de ler JSON com limite de tamanho, preservar ficheiros incompatíveis e escrever através de um temporário.

A ordem é: validar os novos dados, verificar o destino existente, escrever o temporário, descarregar os dados para o sistema e substituir o destino. Se a substituição falhar, o ficheiro antigo mantém-se e o temporário é removido. Isto protege contra escritas interrompidas; não substitui cópias de segurança externas.

O mesmo objeto pode usar memória quando não recebe caminho. Os testes conseguem assim exercitar o comportamento sem tocar nas gravações reais.

## 4. A aplicação coordena os menus

[app.py](../examples/campaign/app.py) contém `CampaignApp`. O seu `mode` distingue título, pausa, opções, confirmação, saída e jogo ativo (`None`). Nos menus, a aplicação desenha a campanha por baixo, mas não chama a atualização do jogo. Por isso, os tiros ficam parados e o relógio não avança.

Há três camadas:

| Camada | Responsabilidade |
|---|---|
| `RangedScene` | Movimento, disparos, inimigos e inventário do nível |
| `CampaignScene` | Sequência de níveis e estatísticas acumuladas |
| `CampaignApp` | Menus, gravação, mensagens e apresentação adicional |

O anfitrião `Game` ganhou um ponto de extensão opcional para eventos da cena e um pedido de saída. Cenas antigas que não usam estes mecanismos continuam a funcionar. O painel F3 mantém prioridade enquanto está aberto, para que Enter e Esc configurem comandos sem ativar um botão do menu por trás.

**Experiência:** pausa quando um projétil está visível. Abre Opções, muda o volume e volta. O projétil continua na mesma posição. N na pausa avança apenas um passo, permitindo observar a simulação lentamente.

## 5. Os efeitos observam acontecimentos

Antes de atualizar a campanha, a aplicação guarda pequenos valores de comparação: vida, mortes, IDs recolhidos e alvos destruídos. Depois da atualização, calcula as diferenças. Um novo ID recolhido produz partículas; vida reduzida produz a tonalidade de dano.

[feedback.py](../platform2d/rendering/feedback.py) guarda apenas estado visual. As partículas usam direções calculadas, têm tempo de vida e são limitadas a 120. Não alteram colisões nem usam o estado aleatório da simulação.

As transições desta fase são entradas suaves sobre o desenho; o jogo já está ativo por baixo. Os menus suspendem a simulação, mas os efeitos por si não o fazem. Desativar os efeitos mantém o mesmo comportamento jogável.

**Experiência:** compara a recolha de uma melhoria com efeitos ligados e reduzidos. A quantidade e o dano final têm de ser iguais.

## 6. Verificar a experiência inteira

Os testes em [test_campaign_release.py](../tests/test_campaign_release.py) cobrem o formato, ficheiros incompatíveis, falha de substituição, confirmações, pausa, rato e ligação ao anfitrião.

[check_campaign_experience.py](../tools/check_campaign_experience.py) acrescenta uma verificação que um teste em memória não consegue oferecer: guarda, fecha a primeira instância e cria outro processo de Python para continuar. Depois termina a campanha e confirma a gravação final.

Os pontos 4 e 5 da sequência proposta — construir um jogo novo contigo e preparar a distribuição — ficam para uma entrega posterior.
