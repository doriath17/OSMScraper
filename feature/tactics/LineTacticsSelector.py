
# =============================================================================
# ENUM DELLE LINE TACTICS
# =============================================================================
from dataclasses import dataclass
from enum import Enum

from rich.console import Console

from GameDifferentialAnalysis import GameDifferentialAnalysis
from GameModule import GameModuleType, GamePlan

console = Console()

class AttackerLine(Enum):
    ATTACK_ONLY = "Solo Attacco"
    SUPPORT_MIDFIELD = "Aiuta il Centrocampo"
    DROP_DEEP = "Rientra in Difesa"

class MidfielderLine(Enum):
    STAY_IN_POSITION = "Rimani in Posizione"
    PUSH_FORWARD = "Avanza / Spingi"
    PROTECT_DEFENCE = "Proteggi la Difesa"

class DefenderLine(Enum):
    DEFEND_DEEP = "Difesa Profonda / Difendi"
    ATTACKING_FULL_BACKS = "Terzini Offensivi"
    SUPPORT_MIDFIELD = "Spingi a Centrocampo"

class LineSelector:
    """
    Selettore delle Line Tactics ottimali in base alla forza relativa k1 e ai moduli
    selezionati (M* e M_adv).
    """

    def __init__(self, differential_analysis: GameDifferentialAnalysis):
        self.attacker_line = LineSelector.calculate_attacker_line(differential_analysis.k, differential_analysis.player.module)
        self.midfielder_line = LineSelector.calculate_midfielder_line(differential_analysis.k, differential_analysis.player.module)
        self.defender_line = LineSelector.calculate_defender_line(differential_analysis.k, differential_analysis.player.module)

    def print(self):
        console.print(f"[bold]Attacker Line:[/bold] {self.attacker_line.value}")
        console.print(f"[bold]Midfielder Line:[/bold] {self.midfielder_line.value}")
        console.print(f"[bold]Defender Line:[/bold] {self.defender_line.value}")

    @staticmethod
    def calculate_attacker_line(k: float, player_module: GameModuleType) -> AttackerLine:
        # =========================================================================
        # 1. LINE TACTICS ATTACCO (Line_att)
        # =========================================================================
        # Se la mediana è numericamente carente (<= 2) o k è molto basso,
        # gli attaccanti devono sacrificarsi in fase di ripiegamento.
        if player_module.value.midfielders <= 2 or k < 0.35:
            line = AttackerLine.DROP_DEEP
        elif k < 0.55 or player_module.value.midfielders == 3:
            line = AttackerLine.SUPPORT_MIDFIELD
        else:
            line = AttackerLine.ATTACK_ONLY
        return line

    @staticmethod
    def calculate_midfielder_line(k: float, player_module: GameModuleType) -> MidfielderLine:
        # =========================================================================
        # 2. LINE TACTICS CENTROCAMPO (Line_mid)
        # =========================================================================
        # Se la difesa è in parità o inferiorità numerica rispetto agli attaccanti avversari,
        # o se k < 0.45, il centrocampo deve fare schermo protettivo.
        if k < 0.45 or player_module.value.defenders <= 3:
            line = MidfielderLine.PROTECT_DEFENCE
        elif k > 0.65 and player_module.value.midfielders >= 4:
            line = MidfielderLine.PUSH_FORWARD
        else:
            line = MidfielderLine.STAY_IN_POSITION
        return line

    @staticmethod
    def calculate_defender_line(k: float, player_module: GameModuleType) -> DefenderLine:
        # =========================================================================
        # 3. LINE TACTICS DIFESA (Line_def)
        # =========================================================================
        # REGOLA RIGIDA: La difesa a 3 (defenders <= 3) NON deve MAI usare terzini offensivi o spingere a centrocampo
        # per evitare lo scoprimento dei braccetti.
        if player_module.value.defenders <= 3 or k < 0.45:
            line = DefenderLine.DEFEND_DEEP
        elif k >= 0.65 and player_module.value.game_plan == GamePlan.WING_PLAY and player_module.value.defenders >= 4:
            line = DefenderLine.ATTACKING_FULL_BACKS
        else:
            line = DefenderLine.SUPPORT_MIDFIELD
        return line