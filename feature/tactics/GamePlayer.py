from typing import Optional

from rich.console import Console

from GameModuleType import GameModuleType
from GamePlan import GamePlan

console = Console()

# NOTE: game_plan is optional because the opponent may not have a plan (e.g., if they are a bot or if the plan is unknown).
# You dont need to pass your game plan to the GamePlayer class, because the GamePlanSelector will handle the selection of the best plan based on the module and context.
class GamePlayer: 
    def __init__(self, base_overall: int, total_bonus: float, module: GameModuleType, game_plan: Optional[GamePlan] = None, 
                 marking: Optional[str] = None, offside_trap: Optional[str] = None):
        self.base_overall = base_overall
        self.total_bonus = total_bonus
        self.module = module
        self.game_plan = game_plan
        self.marking = marking
        self.offside_trap = offside_trap

    def get_effective_overall(self) -> int:
        return int(self.base_overall * (1 + self.total_bonus))

    def print(self):
        console.print(f"[bold]Base Overall:[/bold] {self.base_overall}")
        console.print(f"[bold]Total Bonus:[/bold] {self.total_bonus:.2%}")
        console.print(f"[bold]Module:[/bold] '{self.module.value.code}'")
        console.print(f"[bold]Game Plan:[/bold] '{self.game_plan.value_name if self.game_plan else 'None'}'")
        console.print(f"[bold]Effective Overall:[/bold] {self.get_effective_overall()}")