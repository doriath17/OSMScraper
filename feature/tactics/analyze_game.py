import argparse

from rich.console import Console

from GameDifferentialAnalysis import GameDifferentialAnalysis
from GameModule import parse_module_type
from GamePlayer import GamePlayer
from LineTacticsSelector import LineSelector
from ModuleSelector import ModuleSelector
from SliderSelector import GameSliderSelector
from GameOutcome import GameOutcome    

console = Console() 


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze game tactical approach based on player and opponent stats.")
    parser.add_argument("-pbo", "--player-base-overall", type=int, required=True, help="Base overall of the player")
    parser.add_argument("-ptb", "--player-total-bonus", type=float, required=True, help="Total bonus for the player (as a decimal, e.g., 0.25 for 25%)")
    parser.add_argument("-pm", "--player-module", type=parse_module_type, required=True, help="Module of the player (e.g., '4-4-2', '4-3-3', etc.)")
    parser.add_argument("-obo", "--opponent-base-overall", type=int, required=True, help="Base overall of the opponent")
    parser.add_argument("-otb", "--opponent-total-bonus", type=float, required=True, help="Total bonus for the opponent (as a decimal, e.g., 0.25 for 25%)")
    parser.add_argument("-om", "--opponent-module", type=parse_module_type, required=True, help="Module of the opponent (e.g., '4-4-2', '4-3-3', etc.)")

    # example usage: python ./feature/tactics/analyze_game.py --player-base-overall 80 --player-total-bonus 0.25 --player-module '4-4-2' --opponent-base-overall 75 --opponent-total-bonus 0.10 --opponent-module '4-3-3'
    # example (short) usage: python ./feature/tactics/analyze_game.py -pbo 80 -ptb 0.25 -pm '4-4-2' -obo 75 -otb 0.10 -om '4-3-3'
    args = parser.parse_args()

    ## Create players
    player = GamePlayer(args.player_base_overall, args.player_total_bonus, args.player_module)
    opponent = GamePlayer(args.opponent_base_overall, args.opponent_total_bonus, args.opponent_module)

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