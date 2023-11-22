from Parser import Parser
import logging

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser=Parser.from_file('./Cgrammar.txt')
    parser.print_all_firsts()
    parser.print_all_follows()

if __name__=='__main__':
    main()
