# Fase 18 — espada, defesa e o Guardião

Abre **Jogar-Duelo.cmd → Nova campanha** para experimentar diretamente o Pátio do Guardião. **Jogar-Campanha.cmd** abre a campanha de oito etapas: a Odisseia anterior, seguida deste duelo. **Editor-Duelo.cmd** abre uma cópia por guardar do novo mapa.

## Como jogar

- **J:** golpe de espada. Aproxima-te e prime uma vez por ataque; manter a tecla não repete golpes.
- **L mantido:** defesa frontal, estando no chão. Podes mudar a direção com as setas enquanto defendes.
- **Espaço/Z:** saltar. Ataques e defesa só começam no chão; durante um golpe ou uma defesa, o movimento fica comprometido até os largares/terminares.
- **R:** regressar ao checkpoint. **H:** usar um kit disponível. **F3:** mudar comandos.

No gamepad, os novos comandos usam **L3 para atacar** e **R3 para defender**, porque os botões principais já pertencem às ações anteriores da campanha. Podes remapeá-los em F3; preferências existentes são conservadas.

O Guardião aproxima-se e prepara o ataque levantando uma espada âmbar. **PREPARA**, **GOLPE**, **RECUPERA** e **DEFESA** identificam as suas fases. O golpe só causa dano na janela ativa; a preparação não causa dano. Depois do ataque existe uma abertura para responder. A espada não atravessa paredes sólidas.

Bloquear dentro dos primeiros **0,18 segundos** da defesa provoca um **desvio perfeito** e deixa o Guardião vulnerável durante 0,9 segundos. Larga L e prime J para contra-atacar. Uma defesa mais longa bloqueia o golpe, mas gasta resistência. Defender de costas não protege.

A barra começa com 100 pontos, perde 18 por segundo de defesa e 28 por bloqueio normal. Fora da defesa recupera 22 por segundo. Quando esgota, a guarda cai; sem resistência suficiente, um golpe quebra a defesa e causa dano. Esperar eternamente com L premido não é uma solução segura.

O Guardião também defende e pode desviar ataques precipitados. Tem três pontos de vida. Derrota-o, recolhe o cristal além dele e alcança a saída. Há um checkpoint antes da arena. Não existe dano de contacto: é a espada que atinge; os corpos impedem atravessar o adversário a pé, mas podes saltar por cima.

## Gravação

A derrota do Guardião desencadeia gravação automática e persiste ao carregar ou reaparecer. Vida parcial do inimigo, resistência e golpes em curso são temporários: ao retomar um checkpoint, os combatentes vivos regressam com vida e resistência completas. Recomeçar a campanha repõe o adversário.

A campanha com oito etapas tem uma gravação própria. **Jogar-Odisseia.cmd** conserva a campanha de sete etapas e a respetiva gravação; **Jogar-Expedicao.cmd** e **Jogar-Campanha-Classica.cmd** continuam disponíveis. A demonstração Jogar-Duelo usa outra gravação independente.

## Editor

O duelo é uma opção do perfil **Aventura**, em **Missão / ambiente → Movimento → Espada e defesa**. Desativa primeiro os disparos e escolhe uma câmara horizontal, vertical ou de dois eixos. **Q** escolhe o objeto Guardião; **G** continua a mostrar/ocultar a grelha. Seleciona um Guardião e usa **Vida do guardião…** para definir 1–20 pontos. O corpo mede 24×30.

F5 testa o mesmo controlador, defesa e adversário usados na campanha. Desfazer/refazer e Guardar como funcionam normalmente. A validação verifica modo, tamanho, vida e geometria; não prova automaticamente a solução do combate.

Esta primeira IA de duelo aproxima-se no mesmo patamar, verifica paredes e evita avançar para um precipício. Não salta nem procura caminhos entre plataformas. Desenha uma arena com chão contínuo e testa-a em F5. Ainda não há combos, equipamento de espadas ou mistura de tiros e espada no mesmo duelo.

## Verificação

`tools/check_duel.py` percorre o mapa usando comandos reais: aproximação, desvios, contra-ataques, derrota e saída sem dano nem mortes. Carrega a gravação após a derrota e testa o editor. `tests/test_sword.py` cobre direção da defesa, resistência, interrupções, paredes, pausa, gravação, objetivos e configuração.


A fase **0.21** acrescenta [poses e efeitos para as ações](action-presentation.md), mantendo os comandos e as regras descritos neste guia.
