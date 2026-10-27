"""Retail point-of-sale and discount tracker."""

import logging
import re
from itertools import count

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOGGER = logging.getLogger(__name__)

DEFAULT_PRICES = {"pen": 10, "notebook": 45, "bag": 799, "bottle": 150}

# Accepts only codes such as "total * 0.9" or "total - 50".
PROMO_PATTERN = re.compile(r"^total\s*([*-])\s*(\d+(?:\.\d+)?)$")

class PosSystem:
    """Tracks prices, stock, sales totals and receipts for a small shop."""

    def __init__(self, prices=None):
        self.price_list = dict(prices or DEFAULT_PRICES)
        self.stock = {}
        self.sales_total = 0.0
        self.receipts = []
        self.receipt_lines = []
        self._receipt_numbers = count(1001)

    def process_checkout(self, cart_items, tax_rate=0.05):
        """Total a cart including tax and record the receipt."""
        if not 0 <= tax_rate <= 1:
            raise ValueError(f"Invalid tax rate: {tax_rate}")
        subtotal = 0
        for name, qty in cart_items:
            if name not in self.price_list:
                LOGGER.warning("Unknown item skipped: %s", name)
            elif not isinstance(qty, int) or qty <= 0:
                LOGGER.warning("Invalid quantity for %s: %r", name, qty)
            else:
                subtotal += self.price_list[name] * qty
        total = subtotal * (1 + tax_rate)
        self.receipts.append(total)
        self.sales_total += total
        number = next(self._receipt_numbers)
        self.receipt_lines.append(f"Receipt #{number} total={total:.2f}")
        return total

    def apply_promo_code(self, code_str):
        """Apply a promo code like 'total * 0.9' to the running total."""
        match = PROMO_PATTERN.match(code_str.strip())
        if match is None:
            raise ValueError(f"Unsupported promo code: {code_str!r}")
        operator, value = match.group(1), float(match.group(2))
        if operator == "*" and value > 1:
            raise ValueError("Promo multiplier cannot exceed 1")
        if operator == "*":
            result = self.sales_total * value
        else:
            result = self.sales_total - value
        return max(result, 0.0)

    def update_stock(self, item, qty):
        """Add qty units of a known item to stock."""
        if item not in self.price_list:
            LOGGER.warning("Cannot update stock, unknown item: %s", item)
            return False
        self.stock[item] = self.stock.get(item, 0) + qty
        LOGGER.info("Stock updated for %s by %d", item, qty)
        return True

    def save_receipt_log(self, file="pos_log.txt"):
        """Append all receipt lines to a log file."""
        with open(file, "a", encoding="utf-8") as handle:
            for line in self.receipt_lines:
                handle.write(line + "\n")

    def print_sales(self):
        """Print the running sales total."""
        print(f"Sales so far: {self.sales_total:.2f}")

def main():
    """Run a demo checkout session."""
    pos = PosSystem()
    print("Bill 1:", pos.process_checkout([("pen", 3), ("notebook", 2)]))
    print("Bill 2:", pos.process_checkout([("bag", 1), ("laptop", 1)]))
    print("Bill 3:", pos.process_checkout([("bottle", -4)]))
    try:
        print("Bill 4:", pos.process_checkout([("pen", "2")], tax_rate=-1))
    except ValueError as error:
        print("Bill 4 rejected:", error)
    pos.update_stock("laptop", 5)
    print("After promo:", pos.apply_promo_code("total * 0.9"))
    code = input("Enter promo code (e.g. total - 50): ") or "total - 50"
    try:
        print("After your promo:", pos.apply_promo_code(code))
    except ValueError as error:
        print("Invalid promo code:", error)
    pos.save_receipt_log()
    pos.print_sales()

if __name__ == "__main__":
    main()
