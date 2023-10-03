import itertools

from Transition import Transition
import logging

logger = logging.getLogger("State")


class State:
    __outgoing_transitions: dict[str, list[Transition]]  # SYMBOL, TO
    __incoming_transitions: dict[str, list[Transition]]  # SYMBOL, TO
    is_final: bool
    is_initial: bool
    name: str | None

    def __init__(self, name="noName", is_final=False, is_initial=False):
        self.__outgoing_transitions = {}
        self.__incoming_transitions = {}
        self.is_final = is_final
        self.is_initial = is_initial
        self.name = name

    def add_transition(self, transition: Transition, outgoing: bool) -> bool | None:
        logger.debug(f"Adding transition {transition} to {self.name}")
        determined = True
        if outgoing:
            assert transition.from_state == self
            if transition.symbol in self.__outgoing_transitions:
                if any(
                    map(lambda i: i.to_state == transition.to_state, self.__outgoing_transitions[transition.symbol])
                ):
                    logger.warning(
                        f"Transition from {self.name} to {transition.to_state} "
                        f"with symbol {transition.symbol} already exists, ignoring"
                    )
                    return None
                else:
                    logger.warning(
                        f"FSM isn't determined. "
                        f"Multiple transitions from {self.name} with symbol {transition.symbol} found"
                    )
                    self.__outgoing_transitions[transition.symbol].append(transition)
                    determined = False
            else:
                self.__outgoing_transitions[transition.symbol] = [transition]
        else:
            assert transition.to_state == self
            if transition in list(itertools.chain.from_iterable(self.__incoming_transitions.values())):
                logger.warning(
                    f"Transition to {self.name} from {transition.from_state} "
                    f"with symbol {transition.symbol} already exists, ignoring"
                )
                return None
            if transition.symbol not in self.__incoming_transitions:
                self.__incoming_transitions[transition.symbol] = [transition]
            else:
                self.__incoming_transitions[transition.symbol].append(transition)
        return determined

    def consume_symbol(self, symbol: str) -> "State":
        if not self.__outgoing_transitions.get(symbol):
            raise ValueError(f"No transition found from state {self.name} for symbol {symbol}")
        if len(self.__outgoing_transitions[symbol]) > 1:
            logger.warning(f"More than one transitions from state {self.name} with symbol {symbol} exists.")
        self.__outgoing_transitions[symbol][0].been = True
        next_state = self.__outgoing_transitions[symbol][0].to_state
        logger.debug(f"{self.name}--{symbol}->{next_state.name}")
        return next_state

    def remove_transition(self, transition: Transition):
        if transition.from_state == self:
            logger.debug(f"{self.name} removing outgoing transition to {transition.to_state.name}")
            self.__outgoing_transitions[transition.symbol].remove(transition)
        elif transition.to_state == self:
            logger.debug(f"{self.name} removing incoming transition from {transition.from_state.name}")
            self.__incoming_transitions[transition.symbol].remove(transition)

    @property
    def color(self):
        if self.is_initial:
            return "#2da585"
        elif self.is_final:
            return "#e83b72"
        return "#d89d2b"

    @property
    def ancestors(self) -> list["State"]:
        ancestors = []
        for transition in itertools.chain.from_iterable(self.__incoming_transitions.values()):
            ancestors.append(transition.from_state)
        return ancestors

    @property
    def outgoing_transitions(self) -> list[Transition]:
        return itertools.chain.from_iterable(self.__outgoing_transitions.values())

    @property
    def outgoing_transitions_dict(self) -> dict[str, list[Transition]]:
        return self.__outgoing_transitions

    @property
    def incoming_transitions(self) -> list[Transition]:
        return itertools.chain.from_iterable(self.__incoming_transitions.values())

    @property
    def is_determined(self) -> bool:
        return all([(len(i) <= 1 and all(i)) for i in self.__outgoing_transitions.values()])

    @property
    def is_sink(self) -> bool:
        return not self.__outgoing_transitions or all(tr.to_state == self for tr in self.outgoing_transitions)

    @property
    def is_unreachable(self) -> bool:
        return not list(self.incoming_transitions)

    def __str__(self):
        return f"State <{self.name}, {[str(i) for i in self.outgoing_transitions]}>"

    def __repr__(self):
        return self.__str__()
