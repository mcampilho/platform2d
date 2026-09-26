# Câmara e apresentação do movimento

`platform2d.world.camera.Camera` continua a seguir um corpo dentro dos limites do mapa. A construção aceita três parâmetros opcionais:

```python
camera = Camera(
    viewport=(960, 576),
    bounds=(2400, 576),
    look_ahead=0.18,
    vertical_anchor=0.58,
    responsiveness=7,
)
```

`look_ahead` usa a velocidade horizontal para mostrar mais espaço na direção do movimento. `vertical_anchor` escolhe a altura da personagem no enquadramento e `responsiveness` controla a aproximação suave. Os valores são independentes da física: a câmara lê o corpo, mas nunca altera posição ou velocidade.

## Impulsos visuais

`platform2d.rendering.camera_effects.CameraEffects` produz um pequeno deslocamento interpolado:

```python
effects = CameraEffects(amplitude=7, decay=2.8)
effects.impulse(0.3)

# Em cada passo fixo
effects.update(dt)

# Ao desenhar
offset_x, offset_y = effects.interpolated(alpha)
```

A intensidade aceita valores entre 0 e 1, acumula até ao limite e desaparece com o tempo. A função usa ondas determinísticas, pelo que os testes e repetições recebem os mesmos resultados. A cena decide quais os acontecimentos que justificam um impulso.

No Mundo Vivo, uma aterragem usa intensidade muito baixa, água e gravidade recebem um sinal ligeiro, e o interruptor produz o impulso mais evidente. A opção `effects.camera` permite desligar este recurso desde o início; F6 desliga-o juntamente com os restantes efeitos. Pausa, menus e interface permanecem imóveis.

## Integração numa cena

Mantém o deslocamento fora da câmara de simulação e soma-o apenas às coordenadas usadas para desenhar o mundo. `PrecisionScene` oferece o gancho opcional `camera_offset(alpha)`. Interfaces, texto e menus são desenhados depois e não devem usar esse deslocamento.

Usa impulsos curtos para confirmar acontecimentos, sem os aplicar continuamente. Para acessibilidade, oferece sempre uma opção que os desative e chama `clear()` ao reduzir os efeitos ou reiniciar a cena.
