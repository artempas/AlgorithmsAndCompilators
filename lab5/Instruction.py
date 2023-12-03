import re
from enum import Enum
from functools import cache
from lab1.lab1 import Expression as Calc


class INSTRUCTION_TYPES(Enum):
    PRINT = 'print'
    SCAN = 'scan'
    FOR_LOOP = 'for'
    IF_STATEMENT = 'if'
    ELSE_STATEMENT = 'else'
    ASSIGN = ''


class Instruction:
    instruction: str
    body: list['Instruction']
    variables: dict[str, int]

    def __init__(self, instruction: str):
        self.instruction = instruction
        while self.instruction.startswith(' '):
            self.instruction = self.instruction[1:]
        self.body = []
        self.variables = {}

    def __str__(self):
        return repr(self.instruction) + ('{\n' + '\n'.join(str(i) for i in self.body) + '\n}' if self.body else '')

    @property
    @cache
    def type(self) -> INSTRUCTION_TYPES:
        for i in INSTRUCTION_TYPES:
            if self.instruction.startswith(i.value) and i.value:
                return i
        return INSTRUCTION_TYPES.ASSIGN

    def execute(self, variables: dict[str, int] = None) -> tuple[dict[str, int], bool | None]:
        # print(f"executing {self}")
        if variables is not None:
            self.variables = self.variables | variables
        if_succeed = None
        match self.type:
            case INSTRUCTION_TYPES.PRINT:
                self.process_print()
            case INSTRUCTION_TYPES.SCAN:
                self.process_scan()
            case INSTRUCTION_TYPES.ASSIGN:
                self.process_assign()
            case INSTRUCTION_TYPES.FOR_LOOP:
                self.process_for()
            case INSTRUCTION_TYPES.IF_STATEMENT:
                if_succeed = self.process_if()
            case INSTRUCTION_TYPES.ELSE_STATEMENT:
                self.__process_body()

        return self.variables, if_succeed

    def _calc(self, expr: str) -> int:
        c = Calc(expr)
        c.parse_expression()
        res = c.calculate_expression()
        return int(res)

    def _insert_variables(self, expr: str) -> str:
        res = expr
        for var in re.findall("[a-z_]+", expr, re.RegexFlag.IGNORECASE):
            val = self.variables.get(var)
            if val is None:
                raise Exception(f'Name \'{var}\' is not defined')
            res = res.replace(var, str(val))
        return res

    def process_print(self):
        print(*(self._calc(self._insert_variables(i)) if '"' not in i else i.replace('"','') for i in
                self.instruction.split('print')[1].split(',')))

    def process_scan(self):
        try:
            self.variables[self.instruction.split('scan')[1].replace(' ', '')] = int(input())
        except ValueError:
            raise ValueError("Wrong input. Only integers are supported")

    def process_assign(self, instruction=None) -> [str, int]:
        if instruction:
            var, val = instruction.split('=')
        else:
            var, val = self.instruction.split('=')
        self.variables[var] = self._calc(self._insert_variables(val))
        return var, val

    def __process_body(self):
        if_succeed = None
        for instruction in self.body:
            if instruction.type == INSTRUCTION_TYPES.ELSE_STATEMENT:
                if if_succeed == False:
                    self.variables, if_succeed = instruction.execute(self.variables)
                continue
            self.variables, if_succeed = instruction.execute(self.variables)

    def process_for(self):
        dest: int = self._calc(self._insert_variables(self.instruction.split('to')[1]))
        var, _ = self.process_assign(self.instruction.split('to')[0].replace('for', '').replace(' ', ''))
        while self.variables[var] != dest:
            self.__process_body()

    def process_if(self) -> bool:
        bool_expr = self.instruction.replace('if', '').replace(' ', '')
        matches = re.search('([0-9a-z_+-/*]+)([<>]|==|!=)([0-9a-z_+-/*]+)', bool_expr, re.RegexFlag.IGNORECASE)
        operand1, operator, operand2 = self._calc(self._insert_variables(matches.group(1))), matches.group(
            2), self._calc(self._insert_variables(matches.group(3)))
        bool_res = False
        match operator:
            case ">":
                bool_res = operand1 > operand2
            case "<":
                bool_res = operand1 < operand2
            case "==":
                bool_res = operand1 == operand2
            case "!=":
                bool_res = operand1 != operand2
        if bool_res:
            self.__process_body()
        return bool_res
