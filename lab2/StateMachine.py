import itertools
from functools import cache
from typing import TypeVar

from State import State
from Transition import Transition
import re
from prettytable import PrettyTable
from pyvis.network import Network
import logging

logger = logging.getLogger("StateMachine")


class StateMachine:
    states: dict[str, State]  # name, State
    transitions: list[Transition]
    alphabet: set[str]
    new_transitions: list[Transition]
    new_states: dict[str, State]  # name, state
    is_determined: bool
    graph: Network

    def __init__(self):
        self.transitions = []
        self.new_transitions = []
        self.states = {}
        self.new_states = {}
        self.determined_states = {}
        self.states["q0"] = State("q0", is_initial=True)
        self.is_determined = True
        self.alphabet = set()

    def process_line(self, line: str):
        if not (
            match := re.match(r"(?P<from_state>(?:[qf][0-9]+)+),(?P<symbol>.)=(?P<to_state>(?:[qf][0-9]+)+)", line)
        ):
            if line != "\n":
                raise ValueError(f"Wrong input. Line {line.__repr__()} is unacceptable")
            else:
                return False
        from_state, symbol, to_state = (
            match.group("from_state"),
            match.group("symbol").replace(" ", ""),
            match.group("to_state"),
        )
        if from_state not in self.states:
            self.states[from_state] = State(name=from_state, is_final=from_state[0] == "f")
        if to_state not in self.states:
            self.states[to_state] = State(name=to_state, is_final=to_state[0] == "f")
        if symbol:
            self.alphabet.add(match.group("symbol"))
        else:
            self.is_determined = False
        transition = Transition(self.states[from_state], symbol, self.states[to_state])
        result = self.states[from_state].add_transition(transition, True)
        if result is not None:
            self.is_determined = self.is_determined and result
            self.transitions.append(transition)
            if transition.to_state != transition.from_state:
                self.states[to_state].add_transition(transition, False)
        return True

    def print_graph(self, filename: str, is_new=False):
        self.graph = Network(directed=True)
        if not is_new:
            self.graph.add_nodes(
                list(self.states.keys()),
                shape=["circle"] * len(self.states),
                color=list(map(lambda i: i.color, self.states.values())),
            )
            table = PrettyTable(field_names=["STATE", "SYMBOL", "DESTINATION STATE"])
            graph = {}
            for transition in self.transitions:
                if (transition.from_state.name, transition.to_state.name) in graph:
                    graph[(transition.from_state.name, transition.to_state.name)]["label"] += "," + transition.symbol
                else:
                    graph[(transition.from_state.name, transition.to_state.name)] = {
                        "label": transition.symbol,
                        "color": transition.color,
                        "font": {"size": 20},
                    }
                table.add_row([transition.from_state.name, transition.symbol, transition.to_state.name])
        else:
            self.graph.add_nodes(
                list(self.new_states.keys()),
                shape=["circle"] * len(self.new_states),
                color=list(map(lambda i: i.color, self.new_states.values())),
            )
            table = PrettyTable(field_names=["STATE", "SYMBOL", "DESTINATION STATE"])
            graph = {}
            for transition in self.new_transitions:
                if (transition.from_state.name, transition.to_state.name) in graph:
                    graph[(transition.from_state.name, transition.to_state.name)]["label"] += "," + transition.symbol
                else:
                    graph[(transition.from_state.name, transition.to_state.name)] = {
                        "label": transition.symbol,
                        "color": transition.color,
                        "font": {"size": 20},
                    }
                table.add_row([transition.from_state.name, transition.symbol, transition.to_state.name])
        for edge, options in graph.items():
            self.graph.add_edge(*edge, **options)
        print(table)
        self.graph.show_buttons(True)
        self.graph.set_edge_smooth("dynamic")
        self.graph.show(filename, notebook=False)

    def determine(self) -> bool:
        if self.is_determined:
            logger.info("Graph is finite already")
            return False
        self.__eliminate_empty_transitions()
        # check if determined
        self.is_determined = True
        for node in self.states.values():
            self.is_determined = self.is_determined and node.is_determined
        if self.is_determined:
            logger.info("No need to determine transitions")
            return False
        self.__determine_transitions()
        return True

    def consume_string(self, string: str, new: bool) -> bool:
        states = self.new_states if new else self.states
        for init_state in [i for i in states.values() if i.is_initial]:
            current_state = init_state
            for char in string:
                try:
                    current_state = current_state.consume_symbol(char)
                except ValueError:
                    break
            else:
                if current_state.is_final:
                    return True
        return False

    def __eliminate_empty_transitions(self):
        # Remove all nodes that has only empty transitions incoming
        logger.info("Started removing only empty trans nodes")
        for state in list(self.states.values()).copy():
            if not any(state.incoming_transitions) and not state.is_initial:
                logger.debug(f"Decided to remove state {state}")
                # connect ancestors with descendants according to transitions
                for ancestor in state.ancestors:
                    ancestor.is_final = ancestor.is_final or state.is_final
                    for transition in state.outgoing_transitions:
                        self.__add_transition(Transition(ancestor, transition.symbol, transition.to_state))
                self.__delete_state(state)
        logger.info("Started copying transitions from nodes followed by empty transition")
        # copy transitions from nodes followed by empty transition
        for state in self.states.values():
            for transition in list(state.outgoing_transitions).copy():
                if not transition:
                    state.is_final = transition.to_state.is_final or state.is_final
                    if transition.to_state != transition.from_state:
                        for (
                            copy_transition
                        ) in transition.to_state.outgoing_transitions:  # list all transitions from dest node
                            new_transition = Transition(
                                transition.from_state, copy_transition.symbol, copy_transition.to_state
                            )
                            self.__add_transition(new_transition)
                    self.__delete_transition(transition)

    def __determine_transitions(self):
        logger.info("Started determining transitions")
        states_powerset = powerset(set((self.states.values())))
        for new_state in states_powerset:
            self.__process_subset(new_state)
        while any(
            [
                (state.is_sink and not state.is_final) or (state.is_unreachable and not state.is_initial)
                for state in self.new_states.values()
            ]
        ):
            for name, state in list(self.new_states.items()).copy():
                if (state.is_sink and not state.is_final) or (state.is_unreachable and not state.is_initial):
                    self.__delete_state(state, True)
                else:
                    logger.debug(
                        f"State {state} should not be deleted ({state.is_sink=} {state.is_unreachable=} {state.is_initial=} {state.is_final=}"
                    )

    def __process_subset(self, subset: tuple[State]):
        new_node_name = get_node_name_by_subset(subset)
        logger.debug(f"Processing subset {subset} ({new_node_name})")
        if new_node_name not in self.new_states:
            self.new_states[new_node_name] = State(
                new_node_name, is_initial=all(i.is_initial for i in subset), is_final=any(i.is_final for i in subset)
            )
        for letter in self.alphabet:
            destinations = set()
            for node in subset:
                try:
                    for i in node.outgoing_transitions_dict[letter]:
                        destinations.add(i.to_state)
                except KeyError:
                    continue
            dest_node_name = get_node_name_by_subset(tuple(destinations))
            if dest_node_name not in self.new_states:
                self.new_states[dest_node_name] = State(
                    dest_node_name,
                    is_initial=all(i.is_initial for i in destinations),
                    is_final=any(i.is_final for i in destinations),
                )
            self.__add_transition(
                Transition(self.new_states[new_node_name], letter, self.new_states[dest_node_name]), True
            )
            logger.info(f"Processed letter {letter} for node {new_node_name}. Destination is {dest_node_name}")

    def __delete_transition(self, transition: Transition, is_new=False):
        if not is_new:
            self.states[transition.from_state.name].remove_transition(transition)
            if transition.to_state != transition.from_state:
                self.states[transition.to_state.name].remove_transition(transition)
            self.transitions.remove(transition)
        else:
            self.new_states[transition.from_state.name].remove_transition(transition)
            if transition.to_state != transition.from_state:
                self.new_states[transition.to_state.name].remove_transition(transition)
            self.new_transitions.remove(transition)

    def __delete_state(self, state: State, is_new=False):
        if not is_new:
            for transition in [i for i in self.transitions if i.from_state == state or i.to_state == state]:
                self.__delete_transition(transition)
            del self.states[state.name]
        else:
            for transition in [i for i in self.new_transitions if i.from_state == state or i.to_state == state]:
                self.__delete_transition(transition, True)
            del self.new_states[state.name]

    def __add_transition(self, transition: Transition, is_new=False) -> bool | None:
        logger.debug(f"__add_transition {transition} {is_new=}")
        if not is_new:
            result = self.states[transition.from_state.name].add_transition(transition, True)
            if result is not None:
                self.transitions.append(transition)
                if transition.to_state != transition.from_state:
                    self.states[transition.to_state.name].add_transition(transition, False)
        else:
            result = self.new_states[transition.from_state.name].add_transition(transition, True)
            if result is not None:
                self.new_transitions.append(transition)
                if transition.to_state != transition.from_state:
                    self.new_states[transition.to_state.name].add_transition(transition, False)
        return result


T = TypeVar("T")


def powerset(iterable: set[T]) -> list[tuple[T]]:
    s = list(iterable)
    return list(itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1)))


@cache
def get_node_name_by_subset(subset: list[State]) -> str:
    if not subset:
        return "∅"
    return "".join(i.name for i in sorted(subset, key=lambda i: i.name))
