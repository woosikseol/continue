"""
Python Calculator class for testing chunking
"""
class Calculator:
    """A simple calculator class"""
    
    def __init__(self):
        """Initialize calculator with result 0"""
        self.result = 0
        self.history = []
    
    def add(self, x, y):
        """Add two numbers and return result"""
        result = x + y
        self.history.append(f"Added {x} + {y} = {result}")
        return result
    
    def subtract(self, x, y):
        """Subtract y from x and return result"""
        result = x - y
        self.history.append(f"Subtracted {x} - {y} = {result}")
        return result
    
    def multiply(self, x, y):
        """Multiply two numbers and return result"""
        result = x * y
        self.history.append(f"Multiplied {x} * {y} = {result}")
        return result
    
    def divide(self, x, y):
        """Divide x by y and return result"""
        if y == 0:
            raise ValueError("Cannot divide by zero")
        result = x / y
        self.history.append(f"Divided {x} / {y} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()


def main():
    """Main function to test calculator"""
    calc = Calculator()
    
    # Test basic operations
    print("Testing Calculator:")
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    
    # Show history
    print("\nCalculation History:")
    for entry in calc.get_history():
        print(f"  {entry}")


if __name__ == "__main__":
    main()
