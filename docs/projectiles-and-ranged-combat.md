# Projéteis e combate à distância — versão 0.12.0

Abre **Jogar-Projeteis.cmd** para experimentar **Linha de Defesa**. Destrói os dois alvos e as duas torretas, salta a cobertura central e chega à saída. O jogador tem cinco pontos de vida, munição ilimitada e um checkpoint depois da cobertura.

## Comandos e regras

- **K ou X:** disparar na direção para onde estás virado; manter premido repete os disparos.
- **X do gamepad:** disparar, na configuração de origem do perfil Combate.
- **Setas/A/D:** mover; **Espaço:** saltar.
- **R:** regressar ao checkpoint e recuperar a vida. Alvos já destruídos continuam destruídos; os restantes recuperam toda a resistência.
- **F2:** reiniciar a sessão, incluindo todos os alvos e o ponto inicial.
- **P:** pausa; **N:** avançar um passo durante a pausa; **F3:** configurar comandos; **F10–F12:** som e volume.

Os tiros verdes pertencem ao jogador; os laranja pertencem às torretas. Não há fogo amigo. Cada projétil desaparece no primeiro impacto ou quando esgota a duração. Os blocos sólidos travam os tiros; plataformas finas e rampas atravessáveis por baixo deixam-nos passar em qualquer direção. As torretas disparam horizontalmente quando o jogador está aproximadamente à mesma altura, dentro do alcance e sem um sólido entre ambos. A barra sob cada torreta mostra a recuperação da arma, não uma garantia de que irá disparar naquele instante.

As torretas e os alvos não bloqueiam o corpo nem causam dano por contacto. Os tiros inimigos causam dano e um pequeno impulso; a invulnerabilidade temporária impede que vários impactos simultâneos retirem toda a vida. Um tiro já lançado continua a existir depois de a torreta ser destruída. Morrer, regressar ao checkpoint ou reiniciar limpa os projéteis. A vitória também os remove.

## Criar um nível no editor

**Editor-Combate.cmd** abre uma cópia da demonstração. Em **Novo → Combate** podes começar com chão, spawn e saída. O perfil usa uma sala de 960×576 unidades, sem portas entre salas. Sem alvos, a saída fica logo disponível.

1. Desenha o chão e a cobertura com as ferramentas habituais. Rampas também são aceites.
2. Usa **5 — Alvo** ou **T — Torreta** para colocar os objetos.
3. Seleciona um objeto e abre **Configurar alvo…** ou **Configurar torreta…** no inspetor.
4. Usa **Arma do jogador…**, à esquerda, para ajustar os disparos do jogador.
5. Testa com **F5**. Sai com F5/Escape e guarda com Ctrl+S.

As alterações de configuração entram no histórico de desfazer/refazer e são guardadas no mapa. O teste usa uma cópia; a vida, os tiros e os alvos destruídos não alteram o documento.

| Propriedade | Efeito |
|---|---|
| Velocidade do projétil | Unidades percorridas por segundo |
| Intervalo entre tiros | Tempo mínimo entre disparos; um valor menor dispara mais depressa |
| Duração do projétil | Tempo até desaparecer se não atingir nada |
| Dano por impacto | Resistência retirada por um impacto aceite |
| Resistência do alvo | Dano total necessário para o destruir |
| Alcance da torreta | Distância horizontal de deteção e alcance nominal do seu tiro |

O alcance nominal da arma do jogador é **velocidade × duração**: 620 × 1,5 = **930 unidades** na configuração inicial. O volume físico do projétil pode tocar num alvo um pouco antes de o centro chegar até ele. A cadência é quantizada pelos passos de física a 60 Hz.

## Validação e ficheiros

O mapa usa `editor_profile: "ranged"`. A arma fica em `properties.weapon`, e cada alvo guarda `hp`. As torretas acrescentam `interval`, `projectile_speed` e `range`. Exemplo de configuração da arma:

```json
"properties": {
  "weapon": {"speed": 620, "cooldown": 0.24, "lifetime": 1.5, "damage": 1}
}
```

O editor rejeita parâmetros fora dos limites, resistência fracionária, o ID reservado `player`, objetos fora do mapa e alvos totalmente cobertos por sólidos. Um alvo numa zona de dano pode ser atingido à distância e não é rejeitado por esse motivo. O perfil **não tem pesquisa automática de solução**: F8 verifica a estrutura e avisa para testar o alcance e a acessibilidade em F5. Os avisos não certificam que todos os alvos possam ser destruídos.

Limites da arma: velocidade 1–10000, intervalo 0,02–30 s, duração 0,001–30 s e dano inteiro 1–100. Limites dos alvos: resistência inteira 1–20; nas torretas, intervalo 0,3–10 s, velocidade 60–1800 e alcance 32–1400. O sistema suporta até 128 projéteis simultâneos nesta demonstração; disparos recusados por falta de espaço não ficam em fila.

```powershell
.venv\Scripts\python.exe -m examples.ranged
.venv\Scripts\python.exe -m examples.ranged --map levels/meu-combate.json
.venv\Scripts\python.exe -m examples.editor --profile ranged
```

Os comandos pessoais usam `preferences/ranged.controls.json`. O perfil Combate não guarda progresso em disco. Os perfis anteriores mantêm as suas regras e preferências.

## Limites desta fase

Há um tipo de tiro reto, disparado horizontalmente na demonstração. Não há inventário de armas, carregadores, recarga, munições limitadas, ricochetes, explosões, gravidade dos tiros ou mira com o rato. O núcleo aceita direções bidimensionais, mas os controlos deste jogo usam esquerda/direita. Alvos móveis são suportados pela colisão relativa quando se fornecem as caixas anterior e atual; as torretas e os alvos desta demonstração são estáticos.

Consulta também o [guia de aprendizagem desta fase](learning-projectiles.md), que acompanha o percurso de um disparo no código.
