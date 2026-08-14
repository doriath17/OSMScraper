from model.PlayerPosition import get_position
from model.PlayerRole import get_role
from rich.console import Console
# Transfer history table row example:
# Row 1: ['De Paul', 'Inter Miami CF', 'Legia Warsaw kepler_17', 'CM', '4', '9.4M', '14.5M', '15:12']
# [player_name, from_team, to_team, position, age, base_value, market_value, date_time]

console = Console()

class Transfer:
    def __init__(self, name: str, from_team: str, to_team: str, position: str, age: int, base_value: float, market_value: float, transfer_date: str):
        self.name = name
        self.from_team = from_team
        self.to_team = to_team
        self.position = get_position(position)
        self.role = get_role(self.position)
        self.age = age
        self.base_value: float = float(base_value)
        self.market_value: float = float(market_value)
        self.transfer_date = transfer_date

    def print(self):
        console.print(f"[bold cyan]Transfer: {self.name}\nFrom: {self.from_team}\nTo: {self.to_team}\nPosition: {self.position}\nRole: {self.role}\nAge: {self.age}\nBase Value: {self.base_value}\nMarket Value: {self.market_value}\nTransfer Date: {self.transfer_date}[/bold cyan]")