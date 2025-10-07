/**
 * Java Calculator class for testing chunking
 */
import java.util.ArrayList;
import java.util.List;

public class Calculator {
    private double result;
    private List<String> history;
    
    /**
     * Initialize calculator with result 0
     */
    public Calculator() {
        this.result = 0.0;
        this.history = new ArrayList<>();
    }
    
    /**
     * Add two numbers and return result
     * @param x First number
     * @param y Second number
     * @return Sum of x and y
     */
    public double add(double x, double y) {
        double result = x + y;
        this.history.add(String.format("Added %.2f + %.2f = %.2f", x, y, result));
        return result;
    }
    
    /**
     * Subtract y from x and return result
     * @param x First number
     * @param y Second number
     * @return Difference of x and y
     */
    public double subtract(double x, double y) {
        double result = x - y;
        this.history.add(String.format("Subtracted %.2f - %.2f = %.2f", x, y, result));
        return result;
    }
    
    /**
     * Multiply two numbers and return result
     * @param x First number
     * @param y Second number
     * @return Product of x and y
     */
    public double multiply(double x, double y) {
        double result = x * y;
        this.history.add(String.format("Multiplied %.2f * %.2f = %.2f", x, y, result));
        return result;
    }
    
    /**
     * Divide x by y and return result
     * @param x Dividend
     * @param y Divisor
     * @return Quotient of x and y
     * @throws ArithmeticException if y is zero
     */
    public double divide(double x, double y) throws ArithmeticException {
        if (y == 0) {
            throw new ArithmeticException("Cannot divide by zero");
        }
        double result = x / y;
        this.history.add(String.format("Divided %.2f / %.2f = %.2f", x, y, result));
        return result;
    }
    
    /**
     * Get calculation history
     * @return Copy of calculation history
     */
    public List<String> getHistory() {
        return new ArrayList<>(this.history);
    }
    
    /**
     * Clear calculation history
     */
    public void clearHistory() {
        this.history.clear();
    }
    
    /**
     * Main method to test calculator
     * @param args Command line arguments
     */
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        
        // Test basic operations
        System.out.println("Testing Calculator:");
        System.out.println("5 + 3 = " + calc.add(5, 3));
        System.out.println("10 - 4 = " + calc.subtract(10, 4));
        System.out.println("6 * 7 = " + calc.multiply(6, 7));
        System.out.println("15 / 3 = " + calc.divide(15, 3));
        
        // Show history
        System.out.println("\nCalculation History:");
        for (String entry : calc.getHistory()) {
            System.out.println("  " + entry);
        }
    }
}
