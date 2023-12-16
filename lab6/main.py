from lab4.main import main as lab4
from lab6.Block import Block


def main():
    errors = lab4('./lab6/Grammar.txt', './lab6/test.emark', False)
    with open('./lab6/test.emark') as file:
        content = file.read()
        end_pos = 0
        blocks = []
        while end_pos <= len(content):
            block, end_pos = Block.from_code(content, end_pos)
            blocks.append(block)
    with open('./lab6/template.html') as template:
        with open('./lab6/result.html', 'w') as result:
            content=''
            for block in blocks:
                content+=block.get_html()
            result.write(template.read().replace('{content}', content))



if __name__ == '__main__':
    main()
