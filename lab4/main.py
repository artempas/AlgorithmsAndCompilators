from Parser import Parser
import logging


def main():
    logging.basicConfig(level=logging.INFO)
    parser = Parser.from_file('./Cgrammar.txt')
    parser.print_all_firsts()
    parser.print_all_follows()
    print('\nParsing table')
    parser.print_table(parser.parsing_table,save_to_csv='parsing_table.csv')
    parser.add_sync()
    print('\nSyntax analysis table')
    parser.print_table(parser.syntax_analysis_table, save_to_csv='syntax_analysis.csv')

if __name__ == '__main__':
    main()
