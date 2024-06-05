import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).absolute().parents[3]))

from nemo_skills.finetuning.data_preparation_utils.synthetic_utils import get_eval_func, get_solution_template, get_str_repr, get_template, is_valid_op, is_valid_multiturn_op, operations_map
from nemo_skills.finetuning.data_preparation_utils.solve_expression import solve_expression, merge_solution_steps


def make_question(op, p, q):
    str_p = get_str_repr(p)
    str_q = get_str_repr(q)

    questoin_template = get_template(op)
    solution_template = get_solution_template(op)
    eval_func = get_eval_func(op)

    answer = eval_func(p=p, q=q)
    question = questoin_template.format(p=str_p, q=str_q)
    solution = solution_template.format(p=str_p, q=str_q, ans=answer)

    sample = dict(
        question=question,
        generation=solution,
        expected_answer=answer,
        num_operations=1,
    )

    return sample


def evaluate_expression(expression):
    try:
        result = eval(expression)
        if int(result) == result:
            return int(result)
        return result
    except ZeroDivisionError:
        return None


def generate_number(num_range):
    num = random.randint(num_range[0], num_range[1])
    return f"({num})" if num < 0 else str(num)


def add_parentheses(op, num):
    if op == 'div' and num.count(' ') and not (num[0] == '(' and num[-1] == ')'):
        num = f'({num})'
    if op == 'pow' and num.count(' ') and not (num[0] == '(' and num[-1] == ')'):
        num = f'({num})'
    return num

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
        expression = add_parentheses(op, expression)
        num = add_parentheses(op, num)
        expression = f"{expression} {operations_map[op]} {num}"
    
    return expression


def make_multiturn_question(cfg, num_ops):
    expression = generate_expression((cfg.min_num, cfg.max_num), cfg.allowed_ops, num_ops)
    answer = evaluate_expression(expression)
    solution_steps = solve_expression(expression)
    solution = merge_solution_steps(solution_steps)

    if answer is None:
        return
    
    if int(answer) == answer:
        answer = int(answer)
    else:
        answer = round(answer, 1)
    
    template = get_template("multi")
    expression = template.format(eq=expression)
    assert solution.endswith(str(answer)), f"For some reason solution and answer are different: {solution}, {answer}"

    sample = dict(
        question=expression,
        expected_answer=answer,
        generation=solution,
        num_operations=num_ops
    )
    
    return sample


def gather_questions(allowed_ops, p, q):
    questions = []

    for op in allowed_ops:
        if not is_valid_op(op, p, q):
            continue

        if op == 'div':
            p, q = p * q, p

        question = make_question(op, p, q)
        questions.append(question)

    return questions


def generate_all(cfg):
    samples = []
    for x in range(cfg.min_num, cfg.max_num - 1):
        for y in range(x, cfg.max_num):
            if random.choice([False, True]):
                p, q = x, y
            else:
                p, q = y, x

            questions = gather_questions(cfg.allowed_ops, p, q)
            samples.extend(questions)

    return samples[:cfg.num_samples]


def generate_random(cfg):
    samples = []
    # TODO: Unify this with generate_all function by passing iterator on numbers
    # TODO: rewrite this to iterator
    while len(samples) < cfg.num_samples:
        p = random.randint(cfg.min_num, cfg.max_num)
        q = random.randint(cfg.min_num, cfg.max_num)

        questions = gather_questions(cfg.allowed_ops, p, q)
        samples.extend(questions)

    return samples[:cfg.num_samples]


def generate_multiturn(cfg):
    samples = []
    while len(samples) < cfg.num_samples:
        num_ops = random.choice(cfg.num_ops)
        question = make_multiturn_question(cfg, num_ops)
        samples.append(question)
    
    return samples[:cfg.num_samples]
