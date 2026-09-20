"""Choose one valid nearby interaction by priority, then distance and stable ID."""
from dataclasses import dataclass
from typing import Callable


@dataclass
class Interaction:
    id: str
    label: str
    position: tuple[float,float]
    callback: Callable
    radius: float = 64
    priority: int = 0
    enabled: bool = True


def choose_interaction(body, interactions):
    center = (body.x+body.w/2,body.y+body.h/2)
    candidates = []
    for action in interactions:
        squared = (center[0]-action.position[0])**2+(center[1]-action.position[1])**2
        if action.enabled and squared <= action.radius**2:
            candidates.append((-action.priority,squared,action.id,action))
    return min(candidates,key=lambda item:item[:3])[-1] if candidates else None
