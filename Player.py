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

    def selling_price(self, matchday: int = 0) -> dict:
            max_price = self.max_price()

            # 1. Base Ratio in base al max_price e alla fase di stagione
            # 1. Base Ratio gestito direttamente tramite matchday
            if matchday == 0:  # Pre-stagione
                if max_price <= 10.0:
                    base_ratio = 1.0
                elif max_price <= 15.0:
                    base_ratio = 0.90
                elif max_price <= 24.0:
                    base_ratio = 0.80
                else:
                    base_ratio = 0.70
            else:  # Stagione in corso (matchday >= 1)
                season_discount = 0.0
                if matchday >= 30:
                    season_discount = 0.15
                elif matchday >= 22:
                    season_discount = 0.08
                elif matchday >= 12:
                    season_discount = 0.03

                if max_price <= 5.0:
                    base_ratio = 1.0
                elif max_price <= 12.0:
                    base_ratio = 0.90 - (season_discount * 0.5)
                elif max_price <= 18.0:
                    base_ratio = 0.80 - season_discount
                elif max_price <= 24.0:
                    base_ratio = 0.70 - season_discount
                else:
                    base_ratio = 0.60 - season_discount

            # 2. Modificatore Età (Decade con il progredire dei matchday)
            age_weight = max(0.0, 1.0 - (matchday / 32.0))
            age_mod = 0.0
            if self.age <= 21:
                raw_age_mod = +0.10 if max_price > 18.0 else +0.05
                age_mod = raw_age_mod * age_weight
            elif 22 <= self.age <= 25:
                age_mod = +0.03 * age_weight
            elif 29 <= self.age <= 32:
                age_mod = -0.05
            elif self.age >= 33:
                age_mod = -0.10

            # 3. Modificatore Rating / OVR (Aumenta d'importanza verso fine stagione)
            ovr_weight = 1.0 + (matchday / 35.0)
            ovr_mod = 0.0
            if self.overall >= 88:
                ovr_mod = +0.08 * ovr_weight
            elif self.overall >= 82:
                ovr_mod = +0.04 * ovr_weight
            elif self.overall <= 72:
                ovr_mod = +0.05 if matchday < 15 else -0.05

            # 4. Modificatore Ruolo
            pos_mod = 0.0
            position = getattr(self, 'position', '').upper()
            if position in ['FW', 'ATT']:
                pos_mod = +0.03
            elif position in ['GK', 'POR']:
                pos_mod = -0.05

            # 5. Calcolo finale e Clamp
            total_mod = age_mod + ovr_mod + pos_mod
            raw_final_ratio = base_ratio + total_mod
            final_ratio = min(1.0, max(0.45, raw_final_ratio))

            final_price = round(max_price * final_ratio, 1)

            return {
                "price": final_price,
                "max_price": max_price,
                "final_ratio": round(final_ratio, 3),
                "breakdown": {
                    "base_ratio": round(base_ratio, 3),
                    "age_modifier": round(age_mod, 3),
                    "ovr_modifier": round(ovr_mod, 3),
                    "pos_modifier": round(pos_mod, 3),
                }
            }

    def profit(self, matchday=0):
        return self.selling_price(matchday=matchday)["price"] - self.base_value

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

def get_selling_price(position, age, overall, base_value, matchday=1):
    player = Player(
        name="", position=position, age=age, nationality="", club="",
        attack=0, defense=0, overall=overall, market_value=0.0, base_value=base_value
    )
    return player.selling_price(matchday=matchday)