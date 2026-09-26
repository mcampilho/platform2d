"""Validated sprite-atlas clips with stable anchors and directional mirroring."""
from dataclasses import dataclass
from pathlib import Path

import pygame


@dataclass(frozen=True)
class AnimationClip:
    frames: tuple
    fps: float = 8
    loop: bool = True

    def __post_init__(self):
        if (not self.frames or any(type(frame) is not int or frame < 0 for frame in self.frames)
                or type(self.fps) not in (int,float) or not 0 < self.fps <= 120
                or type(self.loop) is not bool):
            raise ValueError("Animação: clip inválido")


class SpriteAtlas:
    """Load an atlas once and select cached frames without per-frame transforms."""
    def __init__(self,path,frame_size,clips,anchor=(.5,1),directional=True):
        self.path=Path(path)
        if (not isinstance(frame_size,(tuple,list)) or len(frame_size)!=2 or
                any(type(value) is not int or value<=0 for value in frame_size)):
            raise ValueError("Animação: frame_size deve conter dois inteiros positivos")
        if (not isinstance(anchor,(tuple,list)) or len(anchor)!=2 or
                any(type(value) not in (int,float) or not 0<=value<=1 for value in anchor)):
            raise ValueError("Animação: anchor deve conter dois valores entre 0 e 1")
        if type(directional) is not bool:
            raise ValueError("Animação: directional deve ser booleano")
        if not isinstance(clips,dict) or not clips:
            raise ValueError("Animação: é necessário pelo menos um clip")
        self.clips={name:(clip if isinstance(clip,AnimationClip) else AnimationClip(**clip))
                    for name,clip in clips.items()}
        if any(not isinstance(name,str) or not name for name in self.clips):
            raise ValueError("Animação: nomes de clips inválidos")
        try:
            sheet=pygame.image.load(str(self.path))
        except (OSError,pygame.error) as error:
            raise ValueError(f"Animação: não foi possível abrir {self.path.name}: {error}") from error
        width,height=frame_size
        if sheet.get_width()%width or sheet.get_height()%height:
            raise ValueError("Animação: as dimensões do atlas não são múltiplas de frame_size")
        self.frame_size=(width,height)
        self.anchor=tuple(anchor)
        self.directional=directional
        self.frames=[]
        for y in range(0,sheet.get_height(),height):
            for x in range(0,sheet.get_width(),width):
                self.frames.append(sheet.subsurface((x,y,width,height)).copy())
        maximum=max(frame for clip in self.clips.values() for frame in clip.frames)
        if maximum>=len(self.frames):
            raise ValueError(f"Animação: frame {maximum} não existe em {self.path.name}")
        self.mirrored=[pygame.transform.flip(frame,True,False) for frame in self.frames] if directional else self.frames

    @classmethod
    def from_spec(cls,spec):
        return cls(spec.image,spec.frame_size,spec.clips,spec.anchor,spec.directional)

    def frame(self,clip_name,time=0,facing=1):
        try: clip=self.clips[clip_name]
        except KeyError as error: raise ValueError(f"Animação: clip desconhecido: {clip_name}") from error
        step=max(0,int(time*clip.fps))
        position=step%len(clip.frames) if clip.loop else min(step,len(clip.frames)-1)
        index=clip.frames[position]
        return self.frames[index] if facing>=0 or not self.directional else self.mirrored[index]

    def draw(self,surface,position,clip_name,time=0,facing=1):
        image=self.frame(clip_name,time,facing)
        anchor_x=self.anchor[0] if facing>=0 or not self.directional else 1-self.anchor[0]
        left=round(position[0]-anchor_x*image.get_width())
        top=round(position[1]-self.anchor[1]*image.get_height())
        surface.blit(image,(left,top))
        return pygame.Rect(left,top,*image.get_size())
