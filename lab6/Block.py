import re
from typing import Self

from lab6.utils import parse_params
from typing import Literal

ALIGN_MAP = {
    "top": "flex-start",
    "center": "center",
    "bottom": "flex-end",
    'left': 'flex-start',
    'right': 'flex-end'
}


class Cell():

    def __init__(self,
                 width: int = 100,
                 height: int = 100,
                 bgcolor: int = 0,
                 textcolor: int = 1,
                 valign: Literal["top", "center", "bottom"] = "center",
                 halign: Literal["left", "center", "right"] = "center"
                 ):
        self.valign = valign
        self.halign = halign
        self.width: int = width
        self.height: int = height
        self.bgcolor: int = bgcolor
        self.textcolor: int = textcolor
        self.content: str | Block = ''

    def get_lines(self) -> list[str]:
        raise NotImplementedError()

    def override_params(self, **kwargs):
        for (key, val) in kwargs.items():
            if key not in dir(self):
                raise KeyError(f"Unknown attr {key}")
            else:
                self.__setattr__(key, val)

    def add_content(self, code: str):
        if code.startswith('"'):
            self.content = code
        else:
            self.content, _ = Block.from_code(code, **self.__get_kwargs())

    def get_html(self) -> str:
        print(f'getting html for {self.content}')
        if isinstance(self.content, str):
            content = self.content
        elif isinstance(self.content, Block):
            content = self.content.get_html()
        else:
            raise Exception("WATAFAAAAAAAK")
        return f"""<div style="
                height:{self.height}px;
                border:1px solid black;
                width:100%;
                display:flex;
                align-items: {ALIGN_MAP[self.valign]};
                justify-content: {ALIGN_MAP[self.halign]}
                ">{content}</div>"""

    def __get_kwargs(self):
        return {
            "valign": self.valign,
            "halign": self.halign,
            "width": self.width,
            "height": self.height,
            "bgcolor": self.bgcolor,
            "textcolor": self.textcolor
        }


def _get_column_html(column: list[Cell]):
    столбец = f'''
    <div style="
        width: {column[0].width}%;
        height: <TOTAL_HEIGHT>px;
        display: flex;
        flex-direction: column;
        border:1px solid #5eff00;">
    '''
    высота=0
    for cell in column:
        столбец += cell.get_html()
        высота+=int(cell.height)
    столбец=столбец.replace("<TOTAL_HEIGHT>", str(высота))
    столбец += '</div>'
    return столбец, высота


class Block(Cell):
    def __init__(self, columns: int, rows: int, **kwargs):
        super().__init__(**kwargs)
        self.columns: int = columns
        self.rows: int = columns
        self.cells: list[list[Cell]] = [[Cell(**kwargs)] * rows for _ in range(columns)]

    @classmethod
    def from_cell(cls, columns: int, rows: int, cell: Cell):
        return cls(columns, rows,
                   width=cell.width,
                   height=cell.height,
                   bgcolor=cell.bgcolor,
                   textcolor=cell.textcolor,
                   halign=cell.halign,
                   valign=cell.valign)

    @classmethod
    def from_code(cls, code: str, start_position: int = 0, **kwargs) -> (Self, int):
        signatures = re.finditer(r'<[^>]*>', code)
        column_params = {}
        column_n = -1
        row_n = 0
        total_width = 0
        total_height = 0
        generated_block: cls | None = None
        stack_lvl = 0
        last_match = None
        for signature in signatures:
            if signature.start() < start_position:
                continue
            last_match = signature
            if signature.string[signature.start() + 1] == '/':  # closing block
                stack_lvl -= 1
                if not stack_lvl:  # closing block
                    break
                if stack_lvl == 1:  # closing column
                    total_height = 0
                    row_n=0
                if stack_lvl == 2:  # closing row
                    generated_block.cells[column_n][row_n - 1].add_content(
                        code[cell_code_opening.end():signature.start()])
                    print(f"adding content to [{column_n}][{row_n - 1}] {generated_block.cells[column_n][row_n - 1].content}")
            else:  # opening block
                if stack_lvl == 0:  # first block opening
                    name, params = parse_params(code[signature.start():signature.end()])
                    if name != 'block':
                        raise ValueError(f"Expected block to \"block\", got {name}")
                    required_keys = {'columns', 'rows'}
                    if required_keys.difference(set(params.keys())):
                        raise ValueError(f"Missing/too much parameters {required_keys.difference(set(params.keys()))}")
                    generated_block = cls(columns=int(params['columns']), rows=int(params['rows']), **kwargs)
                elif stack_lvl == 1:  # column opening
                    column_opening_position = signature.start()
                    name, params = parse_params(code[signature.start():signature.end()])
                    if 'width' not in params:
                        raise ValueError(f"Width param is required. On {code[signature.start():signature.end()]}")
                    total_width += int(params['width'])
                    if name != 'column':
                        raise ValueError(f"Expected block to \"column\", got {name}")
                    column_params = params
                    column_n += 1
                elif stack_lvl == 2:  # new row opening
                    cell_code_opening = signature
                    name, row_params = parse_params(code[signature.start():signature.end()])
                    if 'height' not in row_params:
                        raise ValueError(f"Height param is required. On {code[signature.start():signature.end()]}")
                    total_height += int(row_params['height'])
                    if name != 'row':
                        raise ValueError(f"Expected block to \"row\", got {name}")
                    try:
                        generated_block.cells[column_n][row_n] = Cell(**column_params)
                        generated_block.cells[column_n][row_n].override_params(**row_params)
                        row_n += 1

                    except IndexError:
                        raise Exception(f"too much columns|rows ({column_n}|{row_n}. On {signature.group(0)}")
                stack_lvl += 1
        for column in generated_block.cells:
            print([cell.content for cell in column])
        return generated_block, start_position + last_match.end()

    def get_html(self) -> str:
        result = f"""
        <div style="
            width: 100%;
            height: {self.height}px;
            display: flex;
            flex-direction: row;
            border:1px solid #ff0000;">
        """
        for column in self.cells:
            хэтэмээл, высота = _get_column_html(column)
            result+=хэтэмээл
        # if int(высота)>int(self.height):
        #     raise ValueError('Children have more height than parent')
        result = result.replace('<ВЫСОТАВЫСОТУШКА>', str(высота))
        result += "</div>"
        return result
