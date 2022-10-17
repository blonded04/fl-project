import ply.lex as lex
import sys
import os

tokens = [
    'START',
    'EPS',
    'EQ',
    'NTERM',
    'SYMBOL',
    'PLUS',
    'ALT',
    'LBR',
    'RBR',
    'LSB',
    'RSB',
    'LFB',
    'RFB',
    'END_OF_LINE',
    'COMMENT'
]


def t_NTERM(t: lex.LexToken):
    r'[A-Za-z][A-Za-z_0-9]*'
    match t.value:
        case "START":
            t.type = "START"
        case "EPS":
            t.type = "EPS"
        case _:
            t.type = "NTERM"
    return t


def t_SYMBOL(t: lex.LexToken):
    r'\"(?:[^\\\"]|\\.)*\"'
    t.value = t.value[1:-1]
    match t.value:
        case "START":
            t.type = "START"
        case "EPS":
            t.type = "EPS"
        case _:
            t.type = "SYMBOL"
    return t


def t_newline(t: lex.LexToken):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t: lex.LexToken):
    print("Error: invalid character: \'{}\'".format(t.value[0]))
    t.lexer.skip(1)


t_EQ = '='
t_PLUS = '\+'
t_ALT = '\|'
t_LBR = '\('
t_RBR = '\)'
t_LSB = '\['
t_RSB = '\]'
t_LFB = '\{'
t_RFB = '\}'
t_COMMENT = '^\#.*'
t_END_OF_LINE = '\;'
t_ignore = ' \t'

lexer = lex.lex()


def main():
    if len(sys.argv) < 2:
        print("Lexer must get at least 1 filename to work with")

    for filename_input in sys.argv[1:]:
        with open(filename_input, "r") as filein, open(os.path.splitext(filename_input)[0] + ".out",
                                                       "w") as file_output:
            lexer_input_data = "".join(filein.readlines())
            lexer.input(lexer_input_data)

            print("CFG: performing lexical analysis for file \"{}\" to file \"{}\"...".format(filename_input,
                                                                                              file_output.name))
            while True:
                token = lexer.token()
                if not token:
                    break
                print(token, file=file_output)


if __name__ == "__main__":
    main()
