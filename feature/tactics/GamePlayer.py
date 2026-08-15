from rich.console import Console

from GameModule import GameModuleType

console = Console()

class GamePlayer: 
    def __init__(self, base_overall: int, total_bonus: float, module: GameModuleType):
        self.base_overall = base_overall
        self.total_bonus = total_bonus
        self.module = module

    def get_effective_overall(self) -> int:
        return int(self.base_overall * (1 + self.total_bonus))

    def print(self):
        console.print(f"[bold]Base Overall:[/bold] {self.base_overall}")
        console.print(f"[bold]Total Bonus:[/bold] {self.total_bonus:.2%}")
        console.print(f"[bold]Module:[/bold] '{self.module.value.code}'")
        console.print(f"[bold]Effective Overall:[/bold] {self.get_effective_overall()}")