"""Ordered campaign progress, independent of rendering and game rules."""
class CampaignProgress:
    def __init__(self, stages):
        self.stages = tuple(stages)
        if not self.stages or any(not isinstance(s,str) or not s for s in self.stages):
            raise ValueError("A campanha precisa de níveis com IDs não vazios.")
        if len(set(self.stages)) != len(self.stages):
            raise ValueError("Os IDs dos níveis não podem repetir-se.")
        self.reset()

    def reset(self):
        self.index = 0
        self.completed = []

    @property
    def current(self):
        return self.stages[self.index]

    @property
    def finished(self):
        return len(self.completed) == len(self.stages)

    def complete(self):
        if self.current in self.completed:
            return False
        self.completed.append(self.current)
        return True

    def advance(self):
        if self.current not in self.completed or self.finished:
            return False
        self.index += 1
        return True
