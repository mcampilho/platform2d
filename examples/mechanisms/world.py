"""Reproducible template, also usable without the editor."""

def room(name):
    return dict(version=1,name=name,tile_size=32,tiles=["."*30]*16+["#"*30]*2,
                objects=[dict(id="start",type="spawn",x=64,y=482)])


def definition():
    control,reactor = room("01 · Alimentação"),room("02 · Reator")
    power = dict(room="control",switch="power")
    sensor = dict(room="reactor",switch="sensor")
    console = dict(room="reactor",switch="console")
    control["objects"] = [control["objects"][0],
        dict(id="power",type="switch",x=250,y=482,w=24,h=30,label="Alimentação",activation="interact"),
        dict(id="crystal_a",type="coin",x=460,y=482),
        dict(id="to_reactor",type="door",x=864,y=454,w=32,h=58,label="REATOR",target_room="reactor",target_entry="start",requires=[power])]
    reactor["objects"] = [reactor["objects"][0],
        dict(id="return",type="door",x=128,y=454,w=32,h=58,label="REGRESSAR",target_room="control",target_entry="start"),
        dict(id="safe",type="checkpoint",x=188,y=482),
        dict(id="sensor",type="switch",x=280,y=496,w=64,h=16,label="Sensor de presença",activation="touch"),
        dict(id="console",type="switch",x=540,y=482,w=24,h=30,label="Consola do reator",activation="interact",requires=[power,sensor]),
        dict(id="crystal_b",type="coin",x=710,y=482),
        dict(id="exit",type="goal",x=864,y=454,w=32,h=58,requires=[console])]
    return dict(version=1,name="Central de Energia",start_room="control",start_entry="start",rooms=dict(control=control,reactor=reactor))
