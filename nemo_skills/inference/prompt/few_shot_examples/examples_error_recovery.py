# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

error_recovery = [
    {
        "question": "Find the radius of the circle with equation $9x^2-18x+9y^2+36y+44=0.$",
        "reference_solution": "First, we factor out the constants of the squared terms to get $9(x^2-2x)+9(y^2+4y)=-44.$\n\nTo complete the square, we need to add $\\left(\\dfrac{2}{2}\\right)^2=1$ after the $-2x$ and $\\left(\\dfrac{4}{2}\\right)^2=4$ after the $4y,$ giving $$9(x-1)^2+9(y+2)^2=-44+9+36=1.$$ Dividing the equation by $9$ gives $$(x-1)^2+(y+2)^2=\\frac{1}{9},$$ so the radius is $\\sqrt{\\frac{1}{9}}=\\boxed{\\frac{1}{3}}.$",
        "level": "Level 5",
        "type": "Algebra",
        "generated_solution": """
First we will complete the square on both $x$ and $y$ terms to convert the equation to one of the standard forms.
{start_code}
from sympy import complete_sqrt, Symbol, solve

x = Symbol('x')
y = Symbol('y')

# define the equation
eq = 9*x**2 - 18*x + 9*y**2 + 36*y + 44

# complete the square
eq = eq.subs(x, x - 1)
eq = eq.subs(y, y + 2)

# simplify the equation
eq = complete_sqrt(eq)

# solve for r
r = solve(eq, x, y)[0][0]
print(r)
{end_code}
{start_code_output}
Execution error: cannot import name 'complete_sqrt' from 'sympy' (/usr/local/lib/python3.10/site-packages/sympy/__init__.py)
{end_code_output}
It looks like the complete_sqrt function is not available. Let's try a different approach.
We can group the $x$ and $y$ terms together and complete the square manually:
- x term: $(3x - 3)^2 = 9(x - 1)^2$
- y term: $(3y + 6)^2 = 9(y + 2)^2$
Then we can add the two terms together and simplify.
{start_code}
from sympy import Symbol, solve, simplify

x, y = Symbol('x'), Symbol('y')

# define the equation
eq = 9*x**2 - 18*x + 9*y**2 + 36*y + 44
term_eq = 9*(x - 1)**2 + 9*(y + 2)**2

simplify(term_eq - eq)
{end_code}
{start_code_output}
1
{end_code_output}
So we get $9(x-1)^2 + 9(y+2)^2 = 1$ and dividing by 9 gives $(x-1)^2 + (y+2)^2 = \\frac{1}{9}$. Therefore, the radius is $\\sqrt{\\frac{1}{9}} = \\boxed{\\frac{1}{3}}$.
""".strip(),
    },
    {
        "question": "A line segment begins at $(1, 3)$. It is 5 units long and ends at the point $(4, x)$ and $x > 0$. What is the value of $x$?",
        "level": "Level 4",
        "type": "Algebra",
        "reference_solution": "We use the distance formula: $$\\sqrt{(4 - 1)^2 + (x - 3)^2} = \\sqrt{3^2 + (x - 3)^2} = \\sqrt{x^2 - 6x + 18} = 5.$$ Squaring both sides and rearranging terms, we find that \\begin{align*}\nx^2 - 6x + 18 &= 25 \\\\\nx^2 - 6x - 7 &= 0\\\\\n(x - 7)(x + 1) &= 0\n\\end{align*} Thus, $x = 7$ or $x = -1$. We are given that $x > 0$, so $x = \\boxed{7}$.\n\n- OR -\n\nNote that the points $(1, 3)$, $(4, 3)$, and $(4, x)$ form a right triangle. We are given that one of the legs has length 3 and the hypotenuse has length 5. This is a Pythagorean triple, so the last leg must have length 4. Therefore, $x = 3 - 4 = -1$ or $x = 3 + 4 = 7$. Since $x > 0$, we find that $x = \\boxed{7}$.",
        "generated_solution": """
We can solve this using sympy.
Let's say the x-coordinate is $\\alpha$. 
{start_code}
import sympy as sp

x1, y1, x2, y2 = sp.symbols('x_1 y_1 x_2 y_2')

# an equation for the line segment
line_eq = sp.Eq(sp.sqrt((x2 - x1)**2 + (y2 - y1)**2), 5)

# values of x1, y1, x2, y2
line_eq = line_eq.subs({x1: 1, y1: 3, x2: 4, y2: x})

# solve for x
sp.solve(line_eq, x)
{end_code}
{start_code_output}
Execution error: name 'x' is not defined
{end_code_output}
We need to define x symbol as well, let's rewrite the code.
{start_code}
import sympy as sp

x1, y1, x2, y2 = sp.symbols('x_1 y_1 x_2 y_2 x')

# an equation for the line segment
line_eq = sp.Eq(sp.sqrt((x2 - x1)**2 + (y2 - y1)**2), 5)

# values of x1, y1, x2, y2
line_eq = line_eq.subs({x1: 1, y1: 3, x2: 4, y2: x})

# solve for x
sp.solve(line_eq, x)
{end_code}
{start_code_output}
[-1, 7]
{end_code_output}
We are given that $x > 0$, so $x = \\boxed{7}$.
""".strip(),
    },
    {
        "question": "The number $a+\sqrt{b}$ and its radical conjugate have a sum of $-4$ and a product of $1$. Find $a+b$.",
        "level": "Level 2",
        "type": "Intermediate Algebra",
        "reference_solution": "The radical conjugate of $a+\sqrt{b}$ is $a-\sqrt{b}$. Hence their sum is $2a$. Then we know that $2a=-4$ which gives us $a=-2$. The product $(a+\sqrt{b})\cdot(a-\sqrt{b})=a^2-b=1.$ Plugging in the value for $a$, we can solve for $b$ to get that $b=(-2)^2-1=3$. Therefore $a+b=-2+3=\boxed{1}$.",
        "generated_solution": """
Let's plug this into sympy and solve for $a$ and $b$.
{start_code}
import sympy as sp

# define the symbols
a, b = sp.symbols('a b')

# the sum of the conjugates is -4 and the product is 1
eq1 = sp.Eq(a + sp.sqrt(b) + a - sp.sqrt(b), -4)
eq2 = sp.Eq(a**2 - b, 1)

# solve for a and b
solutions = sp.solve((eq1, eq2), (a, b))

# evaluate a+b
solutions[a] + solutions[b]
{end_code}
{start_code_output}
Execution error: list indices must be integers or slices, not Symbol
{end_code_output}
Let's look at the solutions variable to see what's going on.
{start_code}
solutions
{end_code}
{start_code_output}
[-2, 3]
{end_code_output}
So the solution is $a=-2$ and $b=3$. Therefore $a+b=-2+3=\\boxed{1}$.
""".strip(),
    },
    {
        "question": "Let $P=  \left( 1 - \frac{1}{2} \right) \left( 1 - \frac{1}{3} \right) \left( 1 - \frac{1}{4} \right) \dotsm \left( 1 - \frac{1}{n} \right)$. What is the value of $P$ if $n=2007$? Express your answer as a common fraction.",
        "level": "Level 2",
        "type": "Intermediate Algebra",
        "reference_solution": "Simplifying each term in $P,$ \[P=\left( \frac{1}{2} \right) \left( \frac{2}{3} \right) \left( \frac{3}{4} \right) \dotsm \left( \frac{n-1}{n} \right) . \]The denominator of each fraction cancels with the numerator of the next fraction, so $P=\frac{1}{n}.$ When $n=2007,$ $P=\boxed{\frac{1}{2007}}.$",
        "generated_solution": """
{start_code}
import sympy as sp

x = sp.symbols('x')
n = 2007
P = x ** (n-1) * sp.prod([x - 1/(i+1) for i in range(n)])
sp.expand(P).simplify()
{end_code}
{start_code_output}
timeout
{end_code_output}
It looks like the computation is taking too long. Let's try a different approach.
{start_code}
from sympy import S, factorial, prod

# the product formula
product = prod(1 - (S(1)/i) for i in range(2,2008))

# as a common fraction
product.as_numer_denom()
{end_code}
{start_code_output}
(1, 2007)
{end_code_output}
So the value of $P$ is $\\boxed{\\frac{1}{2007}}$.
""".strip(),
    },
    {
        "question": "A ball is dropped from 10 feet high and always bounces back up half the distance it just fell. After how many bounces will the ball first reach a maximum height less than 1 foot?",
        "level": "Level 1",
        "type": "Algebra",
        "reference_solution": "We have a geometric sequence with first term 10 and common ratio $1/2$. Any term in this sequence can be represented as $10\cdot\left(\frac{1}{2}\right)^k$, where $k$ is the number of bounces (for example, when $k=1$, $10\cdot\left(\frac{1}{2}\right)^k=5$, or the height of the $k=1^\text{st}$ bounce). We need to find the smallest $k$ such that $10\cdot\left(\frac{1}{2}\right)^k<1$. Through trial and error, we find that $k=4$, so it takes $\boxed{4}$ bounces for the maximum height to be less than 1 foot.",
        "generated_solution": """
Let $x_n$ be the height of the $n$th bounce.
Then $x_0 = 10$, $x_1 = 5$, $x_2 = 5/2$, $x_3 = 5/4$, ...
Each bounce height is just half of the previous one. 
We'll stop when we get to $x_k < 1$.  
Also $x_k = 10 / 2^k$.
Let's use sympy to solve $10 / 2^k < 1$.
{start_code}
from sympy import symbols, Eq, solve

# define the variables
x, k = symbols('x k')

# equation for the height of the nth bounce
eq = Eq(x, 10 / 2**k)

# solve the equation
solutions = solve(eq, k)

# the height should be less than 1
solutions = [solution for solution in solutions if x < 1]

print(solutions[0])
{end_code}
{start_code_output}
Execution error: cannot determine truth value of Relational
{end_code_output}
Looks like x is redundant in the solve function. Let's remove it and try again.
{start_code}
from sympy import symbols, Eq, solve

# define the variables
k = symbols('k')

# equation for the height of the nth bounce
eq = Eq(10 / 2**k, 1)

# solve the equation
solutions = solve(eq, k)

print(solutions[0])
{end_code}
{start_code_output}
1 + log(5)/log(2)
{end_code_output}
We need an integer solution, so let's round up to the nearest integer.
{start_code}
from sympy import ceiling

ceiling(solutions[0])
{end_code}
{start_code_output}
4
{end_code_output}
So it takes $\boxed{4}$ bounces.
""".strip(),
    },
]


examples_map = {
    "math_error_recovery": error_recovery,
}
