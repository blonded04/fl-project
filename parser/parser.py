import ply.yacc as yacc
import sys
import os

from dataclasses import dataclass
from typing import List, Set, TextIO
from lex import tokens


# lexical rules:
#
# elem : non_terminal
#      | symbol
#      | eps
#
# term : elem
#      | term elem
#
# expr : term
#      | expr alt term
#
# rule : non_terminal eq expr

@dataclass
class Nan:
    pass


@dataclass
class Element:
    pass


@dataclass
class NonTerminal(Element):
    name: str


@dataclass
class Symbol(Element):
    value: str


@dataclass
class Eps(Element):
    pass


@dataclass
class Term:
    elements: List[Element]


@dataclass
class Expr:
    terms: List[Term]


@dataclass
class Rule:
    n_term: str
    expr: Expr


@dataclass
class Grammar:
    symbols: Set[str]
    non_terminals: Set[str]
    start: str
    rules: List[Rule]


def show_elem(elem: Symbol | NonTerminal | Eps) -> str:
    if isinstance(elem, Eps):
        return "EPS"
    elif isinstance(elem, NonTerminal):
        return f'{elem.name}'
    elif isinstance(elem, Symbol):
        return f'"{elem.value}"'
    else:
        print(type(elem))
        raise ValueError("Element is not valid")


def make_term(lhs: Term | NonTerminal | Eps | Symbol, rhs: Nan | Symbol | NonTerminal) -> Term:
    if isinstance(lhs, Term):
        if isinstance(rhs, Nan):
            return lhs
        if isinstance(rhs, Term):
            return Term(lhs.elements + rhs.elements)
        return Term(lhs.elements + [rhs])
    if isinstance(rhs, Nan):
        return Term([lhs])
    return Term([lhs, rhs])


def make_expr(lhs: Expr, rhs: Expr) -> Expr:
    if isinstance(lhs, Expr):
        if isinstance(rhs, Nan):
            return lhs
        if isinstance(rhs, Expr):
            return Expr(lhs.terms + rhs.terms)
        return Expr(lhs.terms + [make_term(rhs, Nan())])
    if isinstance(rhs, Nan):
        return Expr([make_term(lhs, Nan())])
    return Expr([make_term(lhs, Nan()), make_term(rhs, Nan())])


def show_expr(expr: Expr) -> str:
    result = ""

    for term in expr.terms:
        result += " + ".join((map(show_elem, term.elements))) + " | "

    result = result[:-3]

    return result


def show_rule(grammar: Grammar, curr_n_term: str) -> str:
    curr_rule_expr = Expr([])
    for rule in grammar.rules:
        if rule.n_term == curr_n_term:
            curr_rule_expr = make_expr(curr_rule_expr, rule.expr)
    if len(curr_rule_expr.terms):
        return curr_n_term + " = " + show_expr(curr_rule_expr) + ";\n"
    return ""


my_grammar = Grammar(set(), set(), "_NotStated_", [])


def find_terminals(expr: Expr) -> set:
    result = set()
    for term in expr.terms:
        for elem in term.elements:
            if isinstance(elem, Symbol):
                result.add(elem.value)
    return result


def find_non_terminals(expr: Expr) -> set:
    result = set()
    for term in expr.terms:
        for elem in term.elements:
            if isinstance(elem, NonTerminal):
                result.add(elem.name)
    return result


def make_grammar(start, rules) -> Grammar:
    symbols = find_terminals(rules[0].expr)
    for i in rules[1:]:
        symbols = symbols.union(find_terminals(i.expr))

    non_terminals = {start}
    for i in rules:
        non_terminals = non_terminals.union(find_non_terminals(i.expr)).union({i.n_term})

    return Grammar(symbols, non_terminals, start, rules)


def set_start(start: str):
    global my_grammar

    my_grammar.non_terminals.add(start)
    my_grammar.start = start


def add_rule(rule: Rule):
    global my_grammar

    my_grammar.rules.append(rule)
    symbols = find_terminals(rule.expr)
    non_terminals = find_non_terminals(rule.expr)
    my_grammar.symbols = my_grammar.symbols.union(symbols)
    my_grammar.non_terminals = my_grammar.non_terminals.union(non_terminals).union({rule.n_term})


def add_new_non_terminal(expr: Expr, bracket: str) -> str:
    global my_grammar

    nterm = "__NT"
    ind = 0
    while (nterm + str(ind)) in my_grammar.non_terminals:
        ind = ind + 1
    non_term = nterm + str(ind)
    add_rule(Rule(non_term, expr))
    match bracket:
        case '[':
            while (nterm + str(ind)) in my_grammar.non_terminals:
                ind = ind + 1
            snd_non_term = nterm + str(ind)

            snd_expr = Expr([Term([Eps()]), Term([NonTerminal(non_term)])])
            add_rule(Rule(snd_non_term, snd_expr))

            return snd_non_term
        case '{':
            while (nterm + str(ind)) in my_grammar.non_terminals:
                ind = ind + 1
            snd_non_term = nterm + str(ind)

            snd_expr = Expr([Term([Eps()]), Term([NonTerminal(snd_non_term), NonTerminal(non_term)])])
            add_rule(Rule(snd_non_term, snd_expr))

            return snd_non_term
        case _:
            return non_term


def show_grammar() -> str:
    global my_grammar

    result = "EBNF Grammar: Syntactic analysis completed\n"
    result += f"List of symbol characters: {my_grammar.symbols}\n"
    result += f"List of non-terminal characters: {my_grammar.non_terminals}\n"
    result += f"Start non-terminal character: {my_grammar.start}\n"
    result += "Rules:\n"
    for grammar_n_term in my_grammar.non_terminals:
        result += show_rule(my_grammar, grammar_n_term)
    return result


def p_grammar(p):
    '''fileline : Start_nonterm
                | rule
                | COMMENT'''


def p_start(p: yacc.YaccProduction):
    '''Start_nonterm : START EQ NON_TERMINAL END_OF_LINE
                     | START EQ NON_TERMINAL END_OF_LINE COMMENT'''

    set_start(p[3])


def p_rule(p: yacc.YaccProduction):
    '''rule : NON_TERMINAL EQ expr END_OF_LINE
            | NON_TERMINAL EQ expr END_OF_LINE COMMENT'''

    add_rule(Rule(p[1], p[3]))


def p_expr(p: yacc.YaccProduction):
    '''expr : expr ALT term
            | term'''

    if len(p) == 4:
        p[0] = make_expr(p[1], p[3])
    else:
        p[0] = make_expr(p[1], Nan())


def p_term(p: yacc.YaccProduction):
    '''term : elem
            | term PLUS elem'''

    if len(p) == 4:
        p[0] = make_term(p[1], p[3])
    else:
        p[0] = make_term(p[1], Nan())


def p_elem_bounded(p: yacc.YaccProduction):
    '''elem : LBR expr RBR
            | LSB expr RSB
            | LFB expr RFB'''

    p[0] = NonTerminal(add_new_non_terminal(p[2], p[1]))


def p_elem_symbol(p: yacc.YaccProduction):
    'elem : SYMBOL'

    p[0] = Symbol(p[1])


def p_elem_non_terminal(p: yacc.YaccProduction):
    'elem : NON_TERMINAL'

    p[0] = NonTerminal(p[1])


def p_elem_eps(p: yacc.YaccProduction):
    'elem : EPS'

    p[0] = Eps()


linecount = 0
fileout: TextIO


def p_error(p):
    global fileout, linecount

    if p is None:
        print(f"Syntax error: No semicolon at the end of rule: line {linecount}")
        print(f"Syntax error: No semicolon at the end of rule: line {linecount}", file=fileout)
    else:
        token = f"{p.type}({p.value}) at {linecount}:{p.lexpos}"
        print(f"Syntax error: Unexpected {token}")
        print(f"Syntax error: Unexpected {token}", file=fileout)
    exit()


parser = yacc.yacc()


def main():
    global fileout, linecount

    if len(sys.argv) < 2:
        print("Parser must get at least 1 filename to work with")

    for filename_input in sys.argv[1:]:
        linecount = 0
        with open(filename_input, "r") as filein, open('.'.join(os.path.splitext(filename_input)[:-1]) + ".prsout",
                                                       "w") as fileout:
            for line in filein.readlines():
                linecount += 1
                if len(line) > 1:
                    if line[-1] == '\n':
                        line = line[:-1]
                    parser.parse(line)
            print(show_grammar(), file=fileout, end='')


if __name__ == "__main__":
    main()
