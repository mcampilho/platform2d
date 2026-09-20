"""Generate original short PCM effects, deterministic and without external assets."""
from math import sin,pi
from pathlib import Path
import random
import struct
import wave

ROOT = Path(__file__).resolve().parents[1]/"platform2d/audio/assets"
RATE = 22050
TONES = {
    "jump":(.16,[240,650]),"land":(.07,[120,70]),"pickup":(.19,[660,990,1320]),
    "checkpoint":(.4,[440,660,880]),"hurt":(.25,[190,70]),"attack":(.12,[500,120]),
    "hit":(.1,[170,90]),"dash":(.15,[220,1000]),"door":(.3,[260,390,520]),
    "switch":(.22,[350,700]),"blocked":(.2,[150,150]),"victory":(.7,[523,659,784,1047]),
    "save":(.24,[523,784]),"load":(.24,[784,523]),"error":(.25,[220,180,130]),
    "shoot":(.10,[1100,280]),
}


def samples(name,duration,notes):
    rng = random.Random(name)
    phase = 0.
    count = int(RATE*duration)
    values = []
    for i in range(count):
        t = i/RATE
        progress = i/count
        if name in {"jump","land","hurt","attack","hit","dash","shoot"}:
            frequency = notes[0]+(notes[-1]-notes[0])*progress
        else:
            frequency = notes[min(len(notes)-1,int(progress*len(notes)))]
        phase += 2*pi*frequency/RATE
        envelope = min(1,t/.008)*min(1,(duration-t)/.035)*(1-.3*progress)
        tone = .85*sin(phase)+.15*sin(phase*2)
        if name in {"attack","hurt","hit","dash"}:
            tone = .65*tone+.35*rng.uniform(-1,1)
        values.append(round(32767*.13*envelope*tone))
    return values


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    for name,(duration,notes) in TONES.items():
        with wave.open(str(ROOT/(name+".wav")),"wb") as out:
            out.setparams((1,2,RATE,0,"NONE","not compressed"))
            values = samples(name,duration,notes)
            out.writeframes(struct.pack("<"+"h"*len(values),*values))
    print(f"Generated {len(TONES)} original PCM effects in {ROOT}.")


if __name__ == "__main__":
    main()
