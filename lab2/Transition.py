from dataclasses import dataclass


@dataclass
class Transition:
    from_state: "State"
    symbol: str
    to_state: "State"
    been: bool = False

    def __bool__(self) -> bool:
        return bool(self.symbol)

    @property
    def color(self):
        if self.been:
            return "#00FF00"
        elif not self.symbol:
            return "#FF0000"
        return "#0000FF"

    def __str__(self):
        return f"{self.from_state.name}-{self.symbol if self.symbol else 'EMP'}->{self.to_state.name}"
