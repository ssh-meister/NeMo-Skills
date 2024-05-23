import random


templates = {
    "+": [
        '{p} + {q}',
        '{p}+{q}',
        'Work out {p} + {q}.',
        'Add {p} and {q}.',
        'Sum of {p} and {q}.',
        'Add together {p} and {q}.',
        'What is {p} plus {q}?',
        'Calculate {p} + {q}.',
        'What is {p} + {q}?',
    ],
    "-": [
        '{p} - {q}',
        '{p}-{q}',
        'Work out {p} - {q}.',
        'What is {p} minus {q}?',
        'Subtract {q} from {p}.',
        'Calculate {p} - {q}.',
        'What is {p} - {q}?',
    ],
    "*": [
        '{p} * {q}',
        '{p}*{q}',
        '{p} \\cdot {q}',
        '{p} \\times {q}',
        'Calculate {p} * {q}.',
        'Work out {p}*{q}.',
        'Multiply {p} and {q}.',
        'Find product of {p} and {q}.',
        'What is the product of {p} and {q}?',
        '{p} times {q}',
        'What is {p} times {q}?',
    ],
    "/": [
        '{p} / {q}',
        '{p}/{q}',
        '{p} : {q}',
        '{p} \\div {q}',
        '{p} \\over {q}',
        '\\frac{{{p}}}{{{q}}}',
        'Divide {p} by {q}.',
        '{p} divided by {q}',
        'What is {p} divided by {q}?',
        'Calculate {p} divided by {q}.',
    ],
    "%": [
        'What is {p}% of {q}?',
        'Calculate {p}% of {q}.',
        'Find {p}% of {q}.',
        '{p}% of {q}',
        'Work out {p}% of {q}.',
    ],
    "**": [
        '{p} ** {q}',
        '{p}**{q}',
        '{p} ^ {q}',
        '{p}^{q}',
        'Calculate {p} to the power of {q}.',
        'What is {p} raised to the power of {q}?',
        '{p} to the power of {q}',
        'Find {p} ^ {q}.',
    ],
    "sqrt": [
        '\\sqrt{{{p}}}',
        '{p} ** 0.5',
        '{p}^0.5',
        '{p} ^ (1/2)',
        '{p}**(1/2)',
        'What is the square root of {p}?',
        'Calculate the square root of {p}.',
        'Find the square root of {p}.',
        'Square root of {p}',
    ],
    "multi": [
        '{eq}',
        'Compute {eq}',
        'What is {eq}?',
        'Calculate {eq}.',
        'Evaluate the expression: {eq}.',
        'Find the result of {eq}.',
        'Work out the value of {eq}.',
        'Determine the result of {eq}.',
    ]
}


def get_template(op):
    template = random.choice(templates[op])
    return template


def is_valid_op(op, p, q):
    if op == "+":
        return p != 0 and q != 0
    elif op == "-":
        return p != 0 and q != 0
    elif op == "*":
        return abs(p * q) <= 1e4
    elif op == "/":
        return q != 0 and round(p / q, 1) == p / q
    elif op == "%":
        return p >= 0 and round(q * p / 100, 1) == q * p / 100
    elif op == "**":
        return 2 <= q <= 10 and - 10000 <= p ** q <= 10000
    elif op == "sqrt":
        return p > 1 and int(p**0.5) == p**0.5


def is_valid_multiturn_op(op, p, q):
    if op == "+":
        return True
    elif op == "-":
        return True
    elif op == "*":
        return abs(p * q) <= 1e4
    elif op == "/":
        return q != 0 and int(p / q) == p / q
    elif op == "**":
        return 2 <= q <= 10 and - 10000 <= p ** q <= 10000
    
def augment_expression(expression):
    mul = random.choice(["*", "\\cdot", "\\times"])
    div = random.choice(["/", "\\div", ":"])
    space = random.choice([" "])
    expression = expression.replace("*", mul)
    expression = expression.replace("/", div)
    expression = expression.replace(" ", space)
    return expression