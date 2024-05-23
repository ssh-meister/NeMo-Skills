import random

from utils import get_template, is_valid_op


def generate_all(args):
    samples = []
    for x in range(args.min_num, args.max_num - 1):
        for y in range(x, args.max_num):
            if random.choice([False, True]):
                p, q = x, y
            else:
                p, q = y, x

            if "+" in args.allowed_ops and is_valid_op("+", p, q):
                template = get_template("+")
                expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
                samples.append(dict(question=expression, expected_answer=p+q, num_operations=1))
        
            if "-" in args.allowed_ops and is_valid_op("-", p, q):
                template = get_template("-")
                expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
                samples.append(dict(question=expression, expected_answer=p-q, num_operations=1))

            if "*" in args.allowed_ops and is_valid_op("*", p, q):
                template = get_template("*")
                expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
                samples.append(dict(question=expression, expected_answer=p*q, num_operations=1))
            
            if "/" in args.allowed_ops and is_valid_op("/", p*q, q):
                template = get_template("/")
                expression = template.format(p=str(p*q) if p*q >= 0 else f"({p*q})", q=str(p) if p >= 0 else f"({p})")
                samples.append(dict(question=expression, expected_answer=q, num_operations=1))
                
            if "%" in args.allowed_ops and is_valid_op("%", p, q):
                template = get_template("%")
                expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
                samples.append(dict(question=expression, expected_answer=p * q / 100, num_operations=1))
            
            if "**" in args.allowed_ops and is_valid_op("**", p, q):
                template = get_template("**")
                expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
                samples.append(dict(question=expression, expected_answer=p**q, num_operations=1))
            
            if "sqrt" in args.allowed_ops and is_valid_op("sqrt", p, q):
                template = get_template("sqrt")
                expression = template.format(p=str(p) if p >= 0 else f"({p})")
                samples.append(dict(question=expression, expected_answer=p**0.5, num_operations=1))
    
    return samples


def generate_random(args):
    samples = []
    for _ in range(args.num_samples):
        p = random.randint(args.min_num, args.max_num)
        q = random.randint(args.min_num, args.max_num)
        
        if "+" in args.allowed_ops and is_valid_op("+", p, q):
            template = get_template("+")
            expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
            samples.append(dict(question=expression, expected_answer=p+q, num_operations=1))
    
        if "-" in args.allowed_ops and is_valid_op("-", p, q):
            template = get_template("-")
            expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
            samples.append(dict(question=expression, expected_answer=p-q, num_operations=1))

        if "*" in args.allowed_ops and is_valid_op("*", p, q):
            template = get_template("*")
            expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
            samples.append(dict(question=expression, expected_answer=p*q, num_operations=1))
        
        if "/" in args.allowed_ops and is_valid_op("/", p*q, q):
            template = get_template("/")
            expression = template.format(p=str(p*q) if p*q >= 0 else f"({p*q})", q=str(p) if p >= 0 else f"({p})")
            samples.append(dict(question=expression, expected_answer=q, num_operations=1))
            
        if "%" in args.allowed_ops and is_valid_op("%", p, q):
            template = get_template("%")
            expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
            samples.append(dict(question=expression, expected_answer=p * q / 100, num_operations=1))
        
        if "**" in args.allowed_ops and is_valid_op("**", p, q):
            template = get_template("**")
            expression = template.format(p=str(p) if p >= 0 else f"({p})", q=str(q) if q >= 0 else f"({q})")
            samples.append(dict(question=expression, expected_answer=p**q, num_operations=1))
        
        if "sqrt" in args.allowed_ops and is_valid_op("sqrt", p, q):
            template = get_template("sqrt")
            expression = template.format(p=str(p) if p >= 0 else f"({p})")
            samples.append(dict(question=expression, expected_answer=p**0.5, num_operations=1))
    
    return samples