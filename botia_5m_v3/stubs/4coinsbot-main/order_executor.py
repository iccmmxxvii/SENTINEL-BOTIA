class OrderExecutor:
    def place(self, side: str, price: float, size: float):
        return {"status": "paper", "side": side, "price": price, "size": size}
