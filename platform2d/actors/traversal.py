"""Optional flight and solid-ledge traversal controllers."""
from .controller import ArcadeController,approach
from platform2d.physics.body import Box


class JetpackController(ArcadeController):
    def before_physics(self,body,actions,dt):
        direction=actions.axis()
        if direction: self.facing=direction
        body.vx=approach(body.vx,direction*self.config.speed,self.config.acceleration*dt)
        thrust='jump' in actions.held
        body.vy=max(-240,min(300,body.vy+(-850 if thrust else 600)*dt))
        self.drop_timer=.15 if 'down' in actions.held else 0
        self.motion_state='fly' if thrust else None

    def after_physics(self,body): pass


class LedgeController(ArcadeController):
    def reset(self):
        super().reset()
        self.anchor=None; self.climb=0; self.cooldown=0
        self.colliders=(); self.bounds=getattr(self,'bounds',(3840,2048))
        self.grabs=0

    def prepare(self,colliders,ladders=()):
        self.colliders=colliders

    def clear_box(self,box):
        return box.x>=0 and box.y>=0 and box.right<=self.bounds[0] and box.bottom<=self.bounds[1] and not any(
            box.overlaps(c.box) for c in self.colliders if not c.one_way)

    def before_physics(self,body,actions,dt):
        self.dt=dt; self.cooldown=max(0,self.cooldown-dt)
        if self.anchor:
            body.vx=body.vy=0; body.on_ground=False
            if self.climb: return
            if 'down' in actions.held:
                self.anchor=None; self.motion_state=None; self.cooldown=.4
                body.vy=60
                return
            if 'jump' in actions.pressed or 'interact' in actions.pressed:
                edge,top,direction=self.anchor
                end_x=edge+2 if direction>0 else edge-body.w-2
                end_y=top-body.h
                vertical=Box(body.x,end_y,body.w,body.y+body.h-end_y)
                horizontal=Box(min(body.x,end_x),end_y,abs(end_x-body.x)+body.w,body.h)
                if self.clear_box(vertical) and self.clear_box(horizontal):
                    self.start=(body.x,body.y); self.end=(end_x,end_y)
                    self.climb=.001; self.motion_state='climb'
            return
        self.motion_state=None
        super().before_physics(body,actions,dt)

    def after_physics(self,body):
        if self.anchor:
            edge,top,direction=self.anchor
            if self.climb:
                self.climb+=self.dt
                t=min(1,self.climb/.3)
                body.y=self.start[1]+(self.end[1]-self.start[1])*min(1,t*2)
                body.x=self.start[0]+(self.end[0]-self.start[0])*max(0,t*2-1)
                if t==1:
                    self.anchor=None; self.climb=0; self.motion_state=None
                    body.on_ground=True; self.cooldown=.2
            else:
                body.x=edge-body.w if direction>0 else edge
                body.y=top-8
            body.vx=body.vy=0
            return
        super().after_physics(body)
        if body.on_ground or body.vy<0 or self.cooldown: return
        for collider in self.colliders:
            if collider.one_way: continue
            r=collider.box
            edge=r.x if self.facing>0 else r.right
            side=body.box.right if self.facing>0 else body.x
            if abs(side-edge)>4 or abs(body.y+8-r.y)>12: continue
            hang=Box(edge-body.w if self.facing>0 else edge,r.y-8,body.w,body.h)
            stand=Box(edge+2 if self.facing>0 else edge-body.w-2,r.y-body.h,body.w,body.h)
            if self.clear_box(hang) and self.clear_box(stand):
                self.anchor=(edge,r.y,self.facing); self.motion_state='hang'; self.grabs+=1
                body.x,body.y=hang.x,hang.y; body.vx=body.vy=0
                self.buffer=self.coyote=0
                break
