import random

from utils import get_eval_func, get_solution_template, get_str_repr, get_template, is_valid_op


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
        solution=solution,
        expected_answer=answer,
        num_operations=1,
    )

    return sample


def gather_questions(allowed_ops, p, q):
    questions = []

    for op in allowed_ops:
        if not is_valid_op(op, p, q):
            continue

        if op == '/':
            p, q = p * q, p

        question = make_question(op, p, q)
        questions.append(question)

    return questions


def generate_all(args):
    samples = []
    for x in range(args.min_num, args.max_num - 1):
        for y in range(x, args.max_num):
            if random.choice([False, True]):
                p, q = x, y
            else:
                p, q = y, x

            questions = gather_questions(args.allowed_ops, p, q)
            samples.extend(questions)

    return samples


def generate_random(args):
    samples = []
    for _ in range(args.num_samples):
        p = random.randint(args.min_num, args.max_num)
        q = random.randint(args.min_num, args.max_num)

        questions = gather_questions(args.allowed_ops, p, q)
        samples.extend(questions)

    return samples
