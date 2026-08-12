# # ['Haaland', '', 'ST', '26', 'Manchester City', '99', '18', '58', '99', '44.6M']

MAX_PRICE_FACTOR = 2.5

class Player: 
    def __init__(self, name, position, age, nationality, club, attack, defense, overall, market_value, base_value=0):
        self.name = name
        self.position = position
        self.age = age
        self.nationality = nationality
        self.club = club
        self.attack = attack
        self.defense = defense
        self.overall = overall
        self.market_value: float = market_value
        self.base_value: float = market_value 

    def __repr__(self):
        return f"Player(name={self.name}, position={self.position}, age={self.age}, nationality={self.nationality}, club={self.club}, attack={self.attack}, defense={self.defense}, overall={self.overall}, market_value={self.market_value})"

    def set_base_value(self, base_value):
        self.base_value = base_value

    def max_price(self) -> float:
        return self.base_value * MAX_PRICE_FACTOR

    def selling_price(self, preseason = False) -> float:
        max_price = self.max_price()

        if preseason:
            if max_price <= 10.0: 
                return max_price # sell at 100% of max price
            elif max_price <= 15.0:
                return max_price * 0.9 # sell at 90% of max price
            elif max_price <= 24.0:
                return max_price * 0.8 # sell at 80% of max price
            else: # max_price > 24.0
                return max_price * 0.7 # sell at 70% of max price

        if max_price <= 5.0:
            return max_price # sell at 100% of max price
        elif max_price <= 12.0: 
            return max_price * 0.9 # sell at 90% of max price
        elif max_price <= 18.0:
            return max_price * 0.8 # sell at 80% of max price
        elif max_price <= 24.0:
            return max_price * 0.7 # sell at 70% of max price
        else: # max_price >= 24.0
            return max_price * 0.6 # sell at 60% of max price

    def profit(self, preseason = False) -> float:
        return self.selling_price(preseason) - self.base_value

def to_number(value): 
    if value is None:
        raise ValueError("Value cannot be None")
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        clean_val = value.strip()
        
        if not clean_val:
            return None

        try:
            if clean_val.endswith("M"):
                return float(clean_val[:-1])
            elif clean_val.endswith("K"):
                return float(clean_val[:-1]) / 1000
            else:
                return float(clean_val)
        except ValueError:
            return None

    return float(value)