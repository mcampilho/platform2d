"""Small bounded visual effects; never changes gameplay or random simulation state."""
import math
import pygame


class Feedback:
    def __init__(self):
        self.particles=[]
        self.flash=0
        self.fade=0
        self.age=0
        self.enabled=True

    def clear(self):
        self.particles.clear(); self.flash=0

    def burst(self,point,color):
        if not self.enabled: return
        for i in range(12):
            angle=i*math.tau/12
            self.particles.append([point[0],point[1],math.cos(angle)*85,math.sin(angle)*85,.45,color])
        self.particles=self.particles[-120:]

    def update(self,dt):
        self.age+=dt
        self.fade=max(0,self.fade-dt)
        self.flash=max(0,self.flash-dt)
        if not self.enabled:
            self.clear(); return
        for p in self.particles:
            p[0]+=p[2]*dt; p[1]+=p[3]*dt; p[3]+=90*dt; p[4]-=dt
        self.particles=[p for p in self.particles if p[4]>0]

    def draw(self,surface):
        if not self.enabled: return
        for x,y,vx,vy,life,color in self.particles:
            pygame.draw.circle(surface,color,(round(x),round(y)),max(1,round(4*life/.45)))
        if self.flash:
            layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
            layer.fill((240,90,100,round(65*self.flash/.2)))
            surface.blit(layer,(0,0))
        if self.fade:
            layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
            layer.fill((8,17,29,round(255*min(1,self.fade/.35))))
            surface.blit(layer,(0,0))
