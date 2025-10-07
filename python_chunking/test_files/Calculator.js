/**
 * JavaScript Calculator class for testing chunking
 */
class Calculator {
    /**
     * Initialize calculator with result 0
     */
    constructor() {
        this.result = 0;
        this.history = [];
    }
    
    /**
     * Add two numbers and return result
     * @param {number} x - First number
     * @param {number} y - Second number
     * @returns {number} Sum of x and y
     */
    add(x, y) {
        const result = x + y;
        this.history.push(`Added ${x} + ${y} = ${result}`);
        return result;
    }
    
    /**
     * Subtract y from x and return result
     * @param {number} x - First number
     * @param {number} y - Second number
     * @returns {number} Difference of x and y
     */
    subtract(x, y) {
        const result = x - y;
        this.history.push(`Subtracted ${x} - ${y} = ${result}`);
        return result;
    }
    
    /**
     * Multiply two numbers and return result
     * @param {number} x - First number
     * @param {number} y - Second number
     * @returns {number} Product of x and y
     */
    multiply(x, y) {
        const result = x * y;
        this.history.push(`Multiplied ${x} * ${y} = ${result}`);
        return result;
    }
    
    /**
     * Divide x by y and return result
     * @param {number} x - Dividend
     * @param {number} y - Divisor
     * @returns {number} Quotient of x and y
     */
    divide(x, y) {
        if (y === 0) {
            throw new Error("Cannot divide by zero");
        }
        const result = x / y;
        this.history.push(`Divided ${x} / ${y} = ${result}`);
        return result;
    }
    
    /**
     * Get calculation history
     * @returns {Array} Copy of calculation history
     */
    getHistory() {
        return [...this.history];
    }
    
    /**
     * Clear calculation history
     */
    clearHistory() {
        this.history = [];
    }
}

/**
 * Main function to test calculator
 */
function main() {
    const calc = new Calculator();
    
    // Test basic operations
    console.log("Testing Calculator:");
    console.log(`5 + 3 = ${calc.add(5, 3)}`);
    console.log(`10 - 4 = ${calc.subtract(10, 4)}`);
    console.log(`6 * 7 = ${calc.multiply(6, 7)}`);
    console.log(`15 / 3 = ${calc.divide(15, 3)}`);
    
    // Show history
    console.log("\nCalculation History:");
    calc.getHistory().forEach(entry => {
        console.log(`  ${entry}`);
    });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Calculator;
} else {
    // Run main if in browser
    main();
}
