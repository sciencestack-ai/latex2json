// Example JavaScript code for testing lstinputlisting
const fibonacci = (n) => {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
};

class Calculator {
    constructor() {
        this.result = 0;
    }

    add(x) {
        this.result += x;
        return this;
    }

    multiply(x) {
        this.result *= x;
        return this;
    }
}

// Usage
console.log(`fib(10) = ${fibonacci(10)}`);
const calc = new Calculator();
console.log(calc.add(5).multiply(3).result); // 15
