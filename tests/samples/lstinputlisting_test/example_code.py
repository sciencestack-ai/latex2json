#!/usr/bin/env python3
"""Example Python script for testing lstinputlisting."""

def factorial(n):
    """Calculate factorial recursively."""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    """Generate Fibonacci sequence."""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

if __name__ == "__main__":
    print(f"5! = {factorial(5)}")
    print(f"First 10 Fibonacci: {list(fibonacci(10))}")
