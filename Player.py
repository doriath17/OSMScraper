# # ['Haaland', '', 'ST', '26', 'Manchester City', '99', '18', '58', '99', '44.6M']

MAX_PRICE_FACTOR = 2.5

class Player: 
    def __init__(self, name, position, age, nationality, club, attack, defense, overall, market_value, base_value=0.0):
        self.name = name
        self.position = position
        self.age = age
        self.nationality = nationality
        self.club = club
        self.attack = attack
        self.defense = defense
        self.overall = overall
        self.market_value: float = market_value
        self.base_value: float = base_value

    def __repr__(self):
        return f"Player(name={self.name}, position={self.position}, age={self.age}, nationality={self.nationality}, club={self.club}, attack={self.attack}, defense={self.defense}, overall={self.overall}, market_value={self.market_value})"

    def set_base_value(self, base_value):
        self.base_value = base_value

    def max_price(self) -> float:
        return self.base_value * MAX_PRICE_FACTOR

    def selling_price(self, preseason: bool = False) -> float:
            max_price = self.max_price()

            # 1. Ratio Base (in base al max_price)
            if preseason:
                if max_price <= 10.0:
                    base_ratio = 1.0
                elif max_price <= 15.0:
                    base_ratio = 0.90
                elif max_price <= 24.0:
                    base_ratio = 0.80
                else:
                    base_ratio = 0.70
            else:
                if max_price <= 5.0:
                    base_ratio = 1.0
                elif max_price <= 12.0:
                    base_ratio = 0.90
                elif max_price <= 18.0:
                    base_ratio = 0.80
                elif max_price <= 24.0:
                    base_ratio = 0.70
                else:
                    base_ratio = 0.60

            # 2. Modificatore Età
            age_mod = 0.0
            if self.age <= 21:
                age_mod = +0.10 if max_price > 18.0 else +0.05
            elif 22 <= self.age <= 25:
                age_mod = +0.03
            elif 29 <= self.age <= 32:
                age_mod = -0.05
            elif self.age >= 33:
                age_mod = -0.10

            # 3. Modificatore Rating (OVR)
            ovr_mod = 0.0
            if self.overall >= 88:
                ovr_mod = +0.08  # Mantiene alto il prezzo per stelle/top player
            elif self.overall >= 82:
                ovr_mod = +0.04
            elif self.overall <= 72:
                ovr_mod = +0.05  # I giocatori scarsi valgono poco, si vendono al max per fare cassa rapida

            # 4. Modificatore Ruolo (self.position: "FW", "MF", "DF", "GK")
            pos_mod = 0.0
            position = getattr(self, 'position', '').upper()
            
            if position in ['FW', 'ATT']:
                pos_mod = +0.03   # Alta domanda di attaccanti
            elif position in ['GK', 'POR']:
                pos_mod = -0.05   # Bassa domanda di portieri, prezzo più aggressivo per sbloccare lo slot

            # 5. Calcolo Ratio Finale e Clamp (tra 0.50 e 1.0)
            total_mod = age_mod + ovr_mod + pos_mod
            final_ratio = min(1.0, max(0.50, base_ratio + total_mod))

            return round(max_price * final_ratio, 1)

    def profit(self, preseason = False) -> float:
        return self.selling_price(preseason) - self.base_value

    def is_stricker(self) -> bool:
        return self.position in ["ST", "CF", "LW", "RW"]

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

def get_selling_price(position, age, overall, base_value, preseason=False):
    player = Player(name="", position=position, age=age, nationality="", club="", attack=0, defense=0, overall=overall, market_value=0.0, base_value=base_value)
    return player.selling_price(preseason)