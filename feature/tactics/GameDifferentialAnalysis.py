## level 1: differential analysis based on the parameter Delta
#
# BOOST MECHANICS
# boost is applied to each player main stat. For example, if a player is 100 and you have the training camp bonus of 25%
# than that player value will be: 100 * (1 + 0.25) = 125
# for this reason, you can calculate the effective overall of a team with this formula: 
#
# NOTE: the bonus is cumulative
# nationality_bonus = 2% (applied only if there are 6 players of the same nationality in the starting 11, the bonus could be 3%)
# stadium_bonus = 0%, 2%, 4%, 6% based on the stadium level (0, 1, 2, 3) -- applied only to the home team
# total_bonus = stadium_bonus + secret_training_bonus (2%) + training_camp_bonus (25%) + nationality_bonus
# >>> effective_overall = base_overall * (1 + total_bonus)
#
# DIFFERENTAL ANALYSIS
# Delta = (player_base_overall * (1 + player_total_bonus)) - (opponent_base_overall * (1 + opponent_total_bonus))
# tactical_approach:
# Svantaggio                Equilibrio              Vantaggio
#     Marcato      Lieve                     Lieve      Marcato
# <-----|--------------|-----------0-----------|--------------|----->
#     -12             -4                      +4             +12
# 
# dunque: 
# delta >= 12: vantaggio marcato
# 4 <= delta < 12: vantaggio lieve
# -4 < delta < 4: equilibrio
# -12 < delta <= -4: svantaggio lieve
# delta <= -12: svantaggio marcato
# 

from enum import Enum
import math

from rich.console import Console


from GamePlayer import GamePlayer

console = Console() 

class TacticalApproach(Enum):
    MARKED_ADVANTAGE = "Vantaggio marcato"
    SLIGHT_ADVANTAGE = "Vantaggio lieve"
    BALANCED = "Equilibrio"
    SLIGHT_DISADVANTAGE = "Svantaggio lieve"
    MARKED_DISADVANTAGE = "Svantaggio marcato"

class GameDifferentialAnalysis:
    def __init__(self, player: GamePlayer, opponent: GamePlayer):
        self.player = player
        self.opponent = opponent
        self.delta = GameDifferentialAnalysis.get_delta(player, opponent)
        self.tactical_approach = GameDifferentialAnalysis.get_tactical_approach(self.delta)
        self.k = GameDifferentialAnalysis.get_k(self.delta)

    def print(self):
        console.print(f"[bold]Delta:[/bold] {self.delta:.2f}")
        console.print(f"[bold]Tactical Approach:[/bold] {self.tactical_approach.value}")
        console.print(f"[bold]Relative Strength (k):[/bold] {self.k:.4f}")
    

    @staticmethod
    def get_delta(player: GamePlayer, opponent: GamePlayer) -> float:
        delta = player.get_effective_overall() - opponent.get_effective_overall()
        return delta

    @staticmethod
    def get_tactical_approach(delta: float) -> TacticalApproach:
        if delta >= 12:
            return TacticalApproach.MARKED_ADVANTAGE
        elif 4 <= delta < 12:
            return TacticalApproach.SLIGHT_ADVANTAGE
        elif -4 < delta < 4:
            return TacticalApproach.BALANCED
        elif -12 < delta <= -4:
            return TacticalApproach.SLIGHT_DISADVANTAGE
        else:  # delta <= -12
            return TacticalApproach.MARKED_DISADVANTAGE

    K_LAMBDA_SCALE = 0.12  # controlla la "ripidezza" della curva sigmoide per k

    @staticmethod
    def get_k(delta: float) -> float:
        """
        k rappresenta la forza relativa della squadra in un intervallo continuo [0.0, 1.0].
        - k = 0.5 indica equilibrio (delta = 0)
        - k > 0.5 indica vantaggio (delta > 0)
        - k < 0.5 indica svantaggio (delta < 0)

        Calcola k tramite una curva sigmoide:
        - delta: (Tuo Effective OVR) - (Adv Effective OVR)
        - lambda_scale: controlla quanto è "ripida" la transizione.
        
        Output: valore continuo tra 0.0 (netta inferiorità) e 1.0 (netto dominio).
        """
        return 1.0 / (1.0 + math.exp(-GameDifferentialAnalysis.K_LAMBDA_SCALE * delta))
