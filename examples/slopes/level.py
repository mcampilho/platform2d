def definition():
    width,height = 64,20
    rows = [["."]*width for _ in range(height)]
    def column(x,y,tile="#"):
        rows[y][x] = tile
        for below in range(y+1,height):
            rows[below][x] = "#"
    for x in range(width):
        if 29 <= x <= 32:
            continue
        if 7 <= x <= 11:
            column(x,22-x,"/")
        elif 12 <= x <= 15:
            column(x,11)
        elif 16 <= x <= 20:
            column(x,x-5,"\\")
        elif 41 <= x <= 43:
            column(x,56-x,"/")
        elif 44 <= x <= 48:
            column(x,13)
        elif 49 <= x <= 51:
            column(x,x-36,"\\")
        else:
            column(x,16)
    objects = [{"id":"start","type":"spawn","x":64,"y":482},
               {"id":"hill-checkpoint","type":"checkpoint","x":432,"y":322},
               {"id":"far-checkpoint","type":"checkpoint","x":1120,"y":482},
               {"id":"exit","type":"goal","x":1824,"y":454,"w":32,"h":58}]
    for index,(x,y) in enumerate(((112,480),(302,392),(400,320),(720,480),(1080,480),(1480,384),(1712,480))):
        objects.append(dict(id=f"crystal-{index+1}",type="coin",x=x,y=y))
    return dict(version=1,name="Colinas",tile_size=32,tiles=["".join(row) for row in rows],objects=objects)
