import re
from typing import Self

from RestorePoint import RestorePoint
from logging import getLogger

logger = getLogger("PDA")


class PushdownAutomata:
    transitions: dict[str, set[str]]  # key: stack symbol, value: list of possibilities
    stack: list[str]
    __string_to_process: list[str]
    alternative_paths: list[RestorePoint]
    path: list[str]

    def __init__(self, transitions: dict[str, set[str]] = None, string_to_process: str = None):
        if transitions:
            if 'E' not in transitions:
                raise ValueError("No initial state (E) provided")
            self.transitions = transitions
        else:
            self.transitions = {}
        self.path = []
        self.alternative_paths = []
        self.stack = ['E']
        self.__string_to_process = []
        self.string_to_process = string_to_process or ''
        logger.info(f"PDA created, {self.transitions=} {self.__string_to_process=}")

    @property
    def string_to_process(self) -> list[str]:
        return self.__string_to_process

    @string_to_process.setter
    def string_to_process(self, value: str | list[str]):
        if isinstance(value, list):
            self.__string_to_process = value
        elif isinstance(value, str):
            self.__string_to_process = [i for i in value[::-1]]

        else:
            raise TypeError(f"string_to_process cannot be of type {type(value)}")

    @classmethod
    def from_file(cls, filename: str) -> Self:
        PDA = cls()
        with open(filename, 'r') as file:
            for line in file:
                line = line.replace('\n', '')
                matched = re.match(r"^([A-Z])>([^|]+(?:\|[^|]+)*)$", line)
                if not matched and not line.startswith(';'):
                    raise ValueError(f"Can't process string {line.__repr__()}")
                elif matched:
                    state = matched.group(1)
                    transitions = matched.group(2).split('|')
                    PDA.add_transition(state, set(transitions))
                elif line.startswith(';'):
                    PDA.string_to_process = line[1:]
        return PDA

    @property
    def is_determined(self):
        return not any(len(i) > 1 for i in self.transitions.values())

    def add_transition(self, stack_symbol: str, new_states: set[str]):
        if stack_symbol in self.transitions:
            self.transitions[stack_symbol] = self.transitions[stack_symbol].union(new_states)
        else:
            self.transitions[stack_symbol] = new_states

    def process_string(self, string_to_process: str = None) -> bool:
        if 'E' not in self.transitions:
            raise ValueError("No initial state (E) provided")
        if self.stack != ['E']:
            logger.info('Stack is not in initial state, emptying')
            self.stack = ['E']
        if self.path:
            logger.info('Path is not empty, emptying')
            self.path=[]
        if string_to_process is not None:
            self.string_to_process = string_to_process
        else:
            if self.__string_to_process is None:
                raise ValueError("No string to process given")
        logger.info(f"Started processing string {self.__string_to_process}")
        while self.string_to_process and (self.stack or self.alternative_paths):
            if not self.stack:
                logger.debug(
                    f"Stack is empty, loading restore point {self.alternative_paths[-1]}")
                self.__load_restore_point(self.alternative_paths.pop())
            stack_top = self.stack.pop()
            logger.debug(f"Got symbol \"{stack_top}\" from the top of stack")
            if re.match("^[A-Z]$", stack_top):
                self.__perform_transition(stack_top)
            else:
                if stack_top == self.string_to_process[-1]:

                    logger.debug("Matched with terminal from string")
                    self.path.append(f'consumed {self.string_to_process.pop()}')
                    continue
                elif self.alternative_paths:
                    logger.debug(
                        f"Didn't matched with terminal from string, loading restore point {self.alternative_paths[-1]}")
                    self.__load_restore_point(self.alternative_paths.pop())
                else:
                    logger.info("Didn't matched with terminal from string, and no restore point found")
                    break
        return not self.string_to_process

    def __load_restore_point(self, restore_point: RestorePoint):
        self.__string_to_process = restore_point.string
        self.stack = restore_point.stack
        self.path = restore_point.path

    def __perform_transition(self, to: str):
        possible_transitions = self.transitions[to]
        for state in possible_transitions:
            new_path = self.path.copy()
            new_path.append(f"{to}->{state}")
            new_stack = self.stack.copy()
            for char in state[::-1]:
                new_stack.append(char)
            self.alternative_paths.append(RestorePoint(string=self.string_to_process.copy(),
                                                       stack=new_stack,
                                                       path=new_path))
        logger.debug(f"Performing transition to {self.alternative_paths[-1]}")
        self.__load_restore_point(self.alternative_paths.pop())
