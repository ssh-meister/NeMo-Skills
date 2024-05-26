import argparse
import json
import random

from generate_multiturn import generate_multiturn
from generate_single_turn import generate_all, generate_random


def create_data(args):
    if args.generation_type in ['all', 'random']:
        assert args.num_ops == [1], 'For `all` and `random` `--num_ops` must be `1`'
    if args.generation_type == 'multiturn':
        assert all(
            op not in args.allowed_ops for op in ["%", "sqrt"]
        ), 'For `multiturn` `--allowed_ops` are +, -, *, /, **'
    if args.generation_type == 'all':
        samples = generate_all(args)
        return samples
    elif args.generation_type == 'random':
        samples = generate_random(args)
        return samples
    elif args.generation_type == 'multiturn':
        samples = generate_multiturn(args)
        return samples
    else:
        raise ValueError(f'Unknown generation type: {args.generation_type}')


def write_jsonl(args, samples):
    random.shuffle(samples)
    with open(args.output_file, 'w') as fout:
        for line in samples[: args.num_samples]:
            fout.write(json.dumps(line) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_file', type=str, required=True)
    parser.add_argument('--min_num', default=1, type=int)
    parser.add_argument('--max_num', default=100, type=int)
    parser.add_argument('--num_samples', default=20000, type=int)
    parser.add_argument('--allowed_ops', nargs='+', default=['+', '-', '/', '*', '%', '**', 'sqrt'])
    parser.add_argument('--num_ops', nargs='+', default=[1], type=int)
    parser.add_argument('--generation_type', choices=['all', 'random', 'multiturn'], default='all')
    parser.add_argument('--random_seed', default=42, type=int)

    args = parser.parse_args()
    random.seed(args.random_seed)

    samples = create_data(args)
    write_jsonl(args, samples)
