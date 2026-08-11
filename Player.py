# # ['Haaland', '', 'ST', '26', 'Manchester City', '99', '18', '58', '99', '44.6M']
class Player: 
    def __init__(self, name, position, age, nationality, club, attack, defense, overall, market_value, base_value="nil"):
        self.name = name
        self.position = position
        self.age = age
        self.nationality = nationality
        self.club = club
        self.attack = attack
        self.defense = defense
        self.overall = overall
        self.market_value = market_value
        self.base_value = base_value

    def __repr__(self):
        return f"Player(name={self.name}, position={self.position}, age={self.age}, nationality={self.nationality}, club={self.club}, attack={self.attack}, defense={self.defense}, overall={self.overall}, market_value={self.market_value})"

    def set_base_value(self, base_value):
        if base_value:
            self.base_value = base_value
        else:
            self.base_value = "nil"