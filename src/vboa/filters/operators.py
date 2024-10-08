# Import python utilities
import operator

mathematic_operators = {
    "+": operator.add,
    "-": operator.sub
}

arithmetic_operators = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne
}

text_operators = {
    "like": "like",
    "notlike": "notlike",
    "in": "in_",
    "notin": "notin_",
}

regex_operators = {
    "regex": ""
}
