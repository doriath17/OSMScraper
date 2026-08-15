import argparse

from rich.console import Console

from GameDifferentialAnalysis import GameDifferentialAnalysis
from GameModuleType import parse_module_type
from GamePlayer import GamePlayer
from LineTacticsSelector import LineSelector
from ModuleSelector import ModuleSelector
from SliderSelector import GameSliderSelector
from GameOutcome import GameOutcome
from GameDefense import parse_bool_flag, parse_marking
from GamePlan import parse_game_plan    

console = Console() 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze game tactical approach based on player and opponent stats.")
    # changing the names: for the player just the names like overall, bonus, module; for the opponent, add a prefix "adv-" to avoid confusion with the player arguments
    parser.add_argument("-o", "--overall", type=int, required=True, help="Base overall of the player")
    parser.add_argument("-b", "--bonus", type=float, required=True, help="Total bonus for the player (as a decimal, e.g., 0.25 for 25%)")
    parser.add_argument("-m", "--module", type=parse_module_type, required=True, help="Module of the player (e.g., '4-4-2', '4-3-3', etc.)")
    parser.add_argument("--adv-o", "--adv-overall", type=int, required=True, help="Base overall of the opponent")
    parser.add_argument("--adv-b", "--adv-bonus", type=float, required=True, help="Total bonus for the opponent (as a decimal, e.g., 0.25 for 25%)")
    parser.add_argument("--adv-m", "--adv-module", type=parse_module_type, required=True, help="Module of the opponent (e.g., '4-4-2', '4-3-3', etc.)")
    parser.add_argument("--adv-marking", type=parse_marking, default=None, help="Marking type of the opponent if known (e.g., 'zona', 'uomo')")
    parser.add_argument("--adv-offside-trap", type=parse_bool_flag, default=None, help="Offside trap of the opponent if known (e.g., 'si', 'no')")
    parser.add_argument(
        "--adv-plan",
        type=parse_game_plan,
        default=None,
        help="Piano di gioco dell'avversario se noto da spia (es. 'fasce', 'counter')"
    )

    #  clear; python ./feature/tactics/analyze_game.py -o 89 -b 0.03 -m '433A' --adv-o 66 --adv-b 0 --adv-m '4231' --adv-plan 'PASSINGGAME' --adv-marking 'UOMO' --adv-offside-trap 'NO'
    args = parser.parse_args()

    ## Create players
    player = GamePlayer(args.overall, args.bonus, args.module)
    opponent = GamePlayer(args.adv_o, args.adv_b, args.adv_m, game_plan=args.adv_plan, marking=args.adv_marking, offside_trap=args.adv_offside_trap)

    ## PRINT PLAYER AND OPPONENT INFO
    console.print("[bold underline]Player Info[/bold underline]")
    player.print()
    console.print("\n[bold underline]Opponent Info[/bold underline]")
    opponent.print()

    ## PIPELINE
    differential_analysis = GameDifferentialAnalysis(player, opponent)
    slider_selector = GameSliderSelector(differential_analysis)
    line_selector = LineSelector(differential_analysis)
    module_selector = ModuleSelector(differential_analysis)
    outcome = GameOutcome(differential_analysis)

    ## PRINT RESULTS
    console.print("\n[bold underline]Game Differential Analysis[/bold underline]")
    differential_analysis.print()
    console.print("\n[bold underline]Slider Selector[/bold underline]")
    slider_selector.print()
    console.print("\n[bold underline]Line Tactics Selector[/bold underline]")
    line_selector.print()
    console.print("\n[bold underline]Module Selector[/bold underline]")
    module_selector.print() 
    console.print("\n[bold underline]Game Outcome[/bold underline]")
    outcome.print()