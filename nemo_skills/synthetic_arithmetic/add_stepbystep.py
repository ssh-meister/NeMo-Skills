import argparse
import json
import re
from collections import Counter

from solve_expression import solve_expression
from tqdm import tqdm


def get_op_counts(counter):
    return sum(counter.get(op, 0) for op in "+-/*")


def extract_expressions(string):
    start = 0
    cur_expr = []
    for idx, c in enumerate(string):
        prev_len = len(cur_expr)
        if c.isspace():
            if cur_expr:
                cur_expr.append(c)
        elif c == '.':
            if cur_expr and cur_expr[-1].isdigit():
                cur_expr.append(c)
            elif cur_expr:
                result = ''.join(cur_expr)
                yield result.rstrip(), start
        elif c.isdigit():
            cur_expr.append(c)
        elif c == '=' and not cur_expr:
            continue
        elif c in '+-/*=()':
            cur_expr.append(c)
        else:
            result = ''.join(cur_expr)
            counter = Counter(result)
            if get_op_counts(counter) >= 2:
                yield result.rstrip(), start
            cur_expr = []
        if prev_len == 0 and len(cur_expr) > 0:
            start = idx


def substitute_arith(args):
    with open(args.input_path) as fin, open(args.output_path, 'w') as fout:
        for line in tqdm(fin):
            sample = json.loads(line)
            output = sample['output']
            new_output = []
            last_end = 0

            for expression, start in extract_expressions(output):
                end = start + len(expression)
                parts = expression.split("=")
                if len(parts) != 2:
                    new_output.append(output[last_end:end])
                    last_end = end
                    continue

                expr, ans = parts
                counter = Counter(expr)
                if get_op_counts(counter) < 2:
                    new_output.append(output[last_end:end])
                    last_end = end
                    continue

                try:
                    solution_steps = solve_expression(expr)
                except:
                    new_output.append(output[last_end:end])
                    last_end = end
                    continue

                solution = []
                for step in solution_steps[:-1]:
                    solution.append(re.sub(r"(-\d+)", r"(\1)", step))
                solution.append(solution_steps[-1].strip())
                solution = " = ".join(solution)
                solution = re.sub(r"\s+", " ", solution)

                try:
                    if eval(solution_steps[-1]) == eval(ans):
                        new_output.append(output[last_end:start] + solution)
                    else:  # skipping solutions with broken math
                        break
                        # new_output.append(output[last_end:end])

                    last_end = end
                except KeyboardInterrupt:
                    raise
                except:
                    new_output.append(output[last_end:end])
                    last_end = end
            else:
                new_output.append(output[last_end:])
                new_output = "".join(new_output)

                sample['output'] = new_output
                fout.write(json.dumps(sample) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path')
    parser.add_argument('--output_path')
    args = parser.parse_args()

    substitute_arith(args)
