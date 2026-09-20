# Áudio e feedback — versão 0.9.0

Os cinco jogos e os testes jogáveis do Atelier passam a usar 15 efeitos originais: salto, aterragem, recolha, checkpoint, dano, ataque, impacto, dash, porta, interruptor, acesso bloqueado, vitória, gravação, carregamento e erro. Cada jogo utiliza os efeitos correspondentes às suas ações.

## Utilização

Abre qualquer um dos atalhos habituais. O volume inicial é 45%.

| Tecla | Ação |
|---|---|
| F10 | Ligar/desligar o som |
| F11 | Reduzir o volume em 10 pontos percentuais |
| F12 | Aumentar o volume em 10 pontos percentuais |

Uma mensagem temporária mostra o estado do som. As preferências duram até fechar a aplicação; no editor mantêm-se entre testes. Também podes arrancar com `--mute` ou `--volume 0.25`, por exemplo:

```powershell
.venv\Scripts\python.exe -m examples.mechanisms --volume 0.25
.venv\Scripts\python.exe -m examples.editor --mute
```

Pausar, perder o foco ou sair do teste interrompe os efeitos. Não ficam sons em espera para tocar mais tarde. Sem dispositivo disponível, o jogo continua e mostra «SOM INDISPONÍVEL». O modo `--headless` começa sempre em silêncio.

## Integração

`platform2d.audio.Audio` carrega os WAV incluídos no pacote, limita a reprodução a seis canais próprios e evita repetições muito rápidas. `play(nome)` devolve se iniciou um efeito; pedidos durante pausa, silêncio ou falta de canais são descartados. `update(dt, paused=...)`, `stop()` e `close()` são responsabilidade da aplicação anfitriã. Fechar o serviço não encerra o mixer de outras funcionalidades.

As cenas têm um `SilentAudio` por predefinição e aceitam um serviço através de `scene.audio`. O anfitrião `Game` injeta o serviço e gere os comandos; o editor partilha-o com a cena de teste. A física comunica acontecimentos de movimento através de `controller.motion_events`; não conhece o dispositivo de som. Recolhas, portas, dano e mecanismos emitem efeitos quando a ação é aceite, evitando repetir o som a cada frame de contacto.

Não há música, áudio espacial nem gravação das preferências nesta entrega. Os efeitos são síntese original, sem dependências externas. Para os reconstruir, executa `.venv\Scripts\python.exe tools\build_audio_assets.py`; **este comando substitui os WAV distribuídos**.

## Verificação

Os testes verificam os ficheiros PCM, os canais do mixer com dispositivo virtual, volume, silêncio, pausa, falha do dispositivo, comandos e ligação às ações. `tools/check_audio_workflow.py` completa os percursos de Salas e Precisão e confirma os acontecimentos sonoros. Os testes automáticos com dispositivo virtual não avaliam a qualidade audível das colunas.


Na versão 0.12.0, o efeito original `shoot` é acrescentado à biblioteca, que passa a ter 16 efeitos. Linha de Defesa usa-o para os disparos do jogador e das torretas.
