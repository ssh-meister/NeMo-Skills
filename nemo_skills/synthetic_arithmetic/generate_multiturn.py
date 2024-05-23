import random

from solve_expression import solve_expression
from utils import is_valid_multiturn_op, get_template


def fill_template(num1, num2, op):
    return f"{num1} {op} {num2}"

def generate_number(num_range):
    num = random.randint(num_range[0], num_range[1])
    return f"({num})" if num < 0 else str(num)

def generate_divisor(num):
    if isinstance(num, str):
        num = int(num.strip('()'))
    elif isinstance(num, float):
        if int(num) != num:
            raise ValueError('Unable to factor decimal number')
        num = int(num)
    assert isinstance(num, int), f'Unable to factor num of type {type(num)}'
    divisors = [i for i in range(2, num + 1) if (num * 10) % i == 0] or [2]
    return random.choice(divisors)

def generate_expression(num_range, ops, num_ops):
    expression = generate_number(num_range)
    num = generate_number(num_range)

    for _ in range(num_ops):
        if expression.count(' ') and random.choice([False, True]):
            expression = f'({expression})'
        
        num = generate_number(num_range)
        if random.choice([False, True]):
            num, expression = expression, num
        num_val = evaluate_expression(num)
        expression_val = evaluate_expression(expression)
        
        op = random.choice([op for op in ops if is_valid_multiturn_op(op, expression_val, num_val)])
        if op == '/' and expression.count(' ') and not (expression[0] == '(' and expression[-1] == ')'):
            expression = f'({expression})'
        if op == '/' and num.count(' ') and not (num[0] == '(' and num[-1] == ')'):
            num = f'({num})'
        expression = fill_template(expression, num, op)
    
    return expression

def evaluate_expression(expression):
    try:
        result = eval(expression)
        if int(result) == result:
            return int(result)
        return result
    except ZeroDivisionError:
        return None

def generate_multiturn(args):
    samples = []
    for _ in range(args.num_samples):
        num_ops = random.choice(args.num_ops)
        expression = generate_expression((args.min_num, args.max_num), args.allowed_ops, num_ops)
        answer = evaluate_expression(expression)
        solution = solve_expression(expression)
        if answer is None:
            continue
        
        if int(answer) == answer:
            answer = int(answer)
        else:
            answer = round(answer, 1)
        
        template = get_template("multi")
        expression = template.format(eq=expression)
        assert solution.endswith(str(answer)), f"For some reason solution and answer are different: {solution}, {answer}"
        samples.append(dict(question=expression, expected_answer=answer, solution=solution, num_operations=num_ops))
    
    return samples
