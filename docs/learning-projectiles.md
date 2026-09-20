# Aprender com a fase 12: do botão ao impacto

A melhor forma de acompanhar esta entrega é seguir **um disparo completo**. Começa por jogar Linha de Defesa e mantém K premido sem mover a personagem. Observa o intervalo entre tiros, a resistência do primeiro alvo e o que acontece aos tiros seguintes quando ele desaparece.

## 1. O botão produz uma intenção

Em `examples/ranged/settings.json`, as teclas K e X correspondem à ação `shoot`. O sistema de input converte teclado e gamepad nas mesmas ações.

Na atualização de `RangedScene`, a condição `"shoot" in actions.held` significa «o jogador quer continuar a disparar». Não significa que um tiro tenha obrigatoriamente de nascer naquele passo: a arma ainda pode estar a recuperar.

**Experiência:** troca temporariamente `held` por `pressed` nessa condição. Passas a pedir um tiro por toque, em vez de repetir ao manter a tecla. Guarda a tua experiência numa cópia e repõe o código antes de continuar os testes existentes.

## 2. A arma decide se pode disparar

Abre [projectiles.py](../platform2d/gameplay/projectiles.py) e procura `Weapon`. Há duas responsabilidades pequenas:

- `update(dt)` reduz o tempo que falta até ao próximo tiro.
- `fire(...)` pede um projétil e só inicia a recuperação se esse projétil tiver sido criado.

`WeaponSpec` contém os dados: velocidade, intervalo, duração, dano e tamanho. Separar os dados da execução permite usar a mesma classe para a arma do jogador e para as torretas.

**Experiência sem alterar código:** no editor, muda o intervalo de 0,24 para 0,5 segundos. Testa e compara. O valor maior dá uma arma mais lenta, não um projétil mais lento: são parâmetros diferentes.

## 3. O projétil guarda o seu próprio estado

`ProjectileSystem.spawn(...)` cria um `Projectile` com posição, velocidade, duração restante, autor e equipa. A direção é normalizada antes de ser multiplicada pela velocidade. Assim, um vetor `(1, 1)` não faz o tiro diagonal viajar mais depressa do que `(1, 0)`.

Um tiro de 620 unidades/s avança cerca de **10,33 unidades por passo de 1/60 s**. A posição anterior é mantida para desenhar a interpolação entre passos, tal como acontece com a personagem.

Na cena, os tiros novos nascem **depois** de avançar os já existentes. Isto evita atribuir a um tiro acabado de nascer um percurso que teria ocorrido antes do momento do disparo.

## 4. Porque não basta testar a posição final?

Imagina um projétil que começa à esquerda de uma parede fina e termina o passo já à direita. Um simples teste de sobreposição na posição final não vê a parede. O projétil atravessaria o obstáculo.

O sistema verifica o **segmento inteiro percorrido**. Para incluir o tamanho do projétil, aumenta o retângulo do obstáculo em metade da largura e da altura do tiro e testa o percurso do centro contra esse retângulo. A função `crossing(...)` devolve a fração do percurso onde começa o contacto.

Por exemplo, `0.25` significa que o contacto ocorre a um quarto do caminho. Entre vários contactos, vence a menor fração. Uma parede ganha um empate com um alvo, para não permitir dano através da cobertura.

Para um alvo móvel, subtrai-se o deslocamento do alvo ao deslocamento do projétil. O teste passa a observar o movimento do tiro **em relação ao alvo**. Este contrato pressupõe que a caixa do alvo mantém o tamanho durante o passo.

**Lê o teste:** em [test_projectiles.py](../tests/test_projectiles.py), `test_fast_shot_hits_one_pixel_wall_and_never_reaches_target` mostra o problema da parede fina com um exemplo pequeno, sem janela Pygame.

## 5. Colidir e causar dano são decisões diferentes

`ProjectileSystem.update(...)` devolve objetos `Impact`. Um impacto identifica o autor, a equipa, o alvo, o ponto e o dano proposto. O sistema remove o projétil, mas **não altera a vida de ninguém**.

Em [scene.py](../examples/ranged/scene.py), `RangedScene.update(...)` interpreta esses impactos. Se o alvo é o jogador, chama `Health.hit(...)`; se é um alvo de treino ou uma torreta, usa a vida desse objeto. A cena também escolhe o som e a pequena animação de impacto.

Esta divisão permite criar outros jogos sem mudar o movimento dos tiros: um projétil poderia ativar um interruptor, pintar uma superfície ou empurrar uma caixa, em vez de retirar vida.

## 6. O editor altera dados, não a simulação

O botão **Arma do jogador…** chama `MapDocument.update_weapon(...)`. O método prepara os novos dados, valida-os e só depois os coloca no documento. O histórico permite desfazer a alteração.

No teste com F5, o editor constrói uma cena a partir de uma cópia desses dados. Destruir uma torreta muda o conjunto `scene.destroyed`, não apaga a torreta do mapa. Ao sair do teste, o documento mantém os objetos originais.

**Experiência:** muda o dano de 1 para 2 e a resistência de um alvo para 3. São necessários dois impactos aceites, porque o primeiro deixa o alvo com 1 ponto de resistência. Depois desfaz as alterações e compara.

## 7. Confirmar o comportamento

Executa:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p test_projectiles.py -v
.venv\Scripts\python.exe -m unittest discover -s tests -p test_ranged.py -v
.venv\Scripts\python.exe tools\check_ranged_route.py
```

O primeiro grupo verifica o núcleo: percurso, equipas, duração, tamanho, alvo mais próximo e limite de projéteis. O segundo verifica regras de jogo: pausa, dano, checkpoint, cobertura e saída. O último usa comandos do jogador para completar a demonstração através do editor e confirma que o mapa ficou intacto.

Para estudar o código por ordem: `settings.json` → `WeaponSpec` → `Weapon` → `ProjectileSystem.update` → `RangedScene.update` → `MapDocument.update_weapon`. Não precisas de compreender o editor inteiro para experimentar esta mecânica.
