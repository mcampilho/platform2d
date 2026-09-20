"""Optional swimming and a collectable second jump, using ordinary collisions."""
from .controller import ArcadeController,approach


class SwimController(ArcadeController):
    def reset(self):
        super().reset(); self.submerged=False; self.current=0

    def before_physics(self,body,actions,dt):
        if not self.submerged:
            self.motion_state=None
            return super().before_physics(body,actions,dt)
        direction=actions.axis()
        if direction: self.facing=direction
        vertical=int('down' in actions.held)-int('jump' in actions.held or 'up' in actions.held)
        body.vx=approach(body.vx,direction*135+self.current,650*dt)
        body.vy=approach(body.vy,vertical*145-15,550*dt)
        self.motion_state='fly'; self.buffer=self.coyote=self.drop_timer=0


class ExploreController(ArcadeController):
    def reset(self):
        super().reset(); self.enabled=False; self.extra_used=False

    def before_physics(self,body,actions,dt):
        grounded=body.on_ground
        if grounded: self.extra_used=False
        extra=self.enabled and not grounded and self.coyote<=0 and not self.extra_used and 'jump' in actions.pressed
        super().before_physics(body,actions,dt)
        if extra:
            self.jump(body); self.extra_used=True
