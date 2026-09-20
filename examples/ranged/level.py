def definition():
    rows = [["."]*30 for _ in range(18)]
    rows[16] = ["#"]*30
    rows[17] = ["#"]*30
    rows[14][13] = rows[15][13] = "#"
    return dict(version=1,name="Linha de Defesa",editor_profile="ranged",tile_size=32,
        properties={"weapon":{"speed":620,"cooldown":.24,"lifetime":1.5,"damage":1}},
        tiles=["".join(row) for row in rows],objects=[
            dict(id="start",type="spawn",x=64,y=482),
            dict(id="training",type="target",x=215,y=482,w=24,h=30,hp=2),
            dict(id="sentry-a",type="turret",x=342,y=482,w=28,h=30,hp=3,interval=1.25,projectile_speed=230,range=320),
            dict(id="safe-point",type="checkpoint",x=490,y=482),
            dict(id="sentry-b",type="turret",x=672,y=482,w=28,h=30,hp=3,interval=1.1,projectile_speed=260,range=400),
            dict(id="final-target",type="target",x=824,y=482,w=24,h=30,hp=2),
            dict(id="exit",type="goal",x=910,y=454,w=32,h=58)])
