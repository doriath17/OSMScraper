import argparse
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List

from GameModuleType import GameModuleType
from GamePlan import GamePlan


class MarkingType(Enum):
    ZONA = "Marcatura a Zona"
    UOMO = "Marcatura a Uomo"


class OffsideTrap(Enum):
    YES = "Sì"
    NO = "No"


@dataclass(frozen=True)
class DefensiveSetup:
    marking: MarkingType
    offside_trap: OffsideTrap
    score: float
    reasoning: List[str]  # Per spiegare all'utente il perché della scelta

class DefensiveInstructionsSelector:

    @staticmethod
    def evaluate_defensive_setup(
        my_module: GameModuleType,
        my_plan: GamePlan,
        k: float,
        adv_module: GameModuleType,
        adv_plan: Optional[GamePlan] = None,
        adv_marking: Optional[MarkingType] = None,  
        adv_offside: Optional[OffsideTrap] = None   
    ) -> DefensiveSetup:
        """
        Calcola la combinazione ottimale di Marcatura e Trappola del Fuorigioco
        per un dato assetto di squadra e l'avversario.
        """
        my_defenders: int = my_module.value.defenders
        adv_forwards: int = adv_module.value.attackers
        reasons: List[str] = []

        # --- LOGICA MARCATURA ---
        if my_defenders <= adv_forwards:
            marking = MarkingType.UOMO
            reasons.append(f"Marcatura a Uomo: Parità/Svantaggio numerico ({my_defenders} dif vs {adv_forwards} att).")
        else:
            marking = MarkingType.ZONA
            reasons.append(f"Marcatura a Zona: Superiorità numerica ({my_defenders} dif vs {adv_forwards} att).")

        if adv_plan == GamePlan.PASSING_GAME and marking == MarkingType.UOMO:
            marking = MarkingType.ZONA
            reasons.append("Forzato passaggio a Zona: L'avversario fa Passing Game, l'uomo aprirebbe troppi varchi.")

        # --- LOGICA TRAPPOLA DEL FUORIGIOCO ---
        if my_defenders >= 5:
            offside = OffsideTrap.NO
            reasons.append("Fuorigioco NO: Difesa a 5 troppo folta per la salita sincronizzata.")
        elif k < 0.35:
            offside = OffsideTrap.NO
            reasons.append("Fuorigioco NO: Squadra in svantaggio di forza (k basso).")
        elif adv_plan == GamePlan.COUNTER_ATTACK:
            offside = OffsideTrap.NO
            reasons.append("Fuorigioco NO: Avversario in Contropiede, alzare la linea è ad alto rischio.")
        elif marking == MarkingType.UOMO:
            offside = OffsideTrap.NO
            reasons.append("Fuorigioco NO: Incompatibile con la Marcatura a Uomo.")
        
        # Sfruttiamo adv_offside per confermare la trappola del fuorigioco
        elif adv_offside == OffsideTrap.YES and my_defenders in (3, 4) and k >= 0.45:
            offside = OffsideTrap.YES
            reasons.append("Fuorigioco SÌ: L'avversario usa il Fuorigioco; compatibile con una linea difensiva alta e compatta.")
        elif adv_plan in (GamePlan.LONG_BALL, GamePlan.SHOOT_ON_SIGHT) and my_defenders in (3, 4):
            offside = OffsideTrap.YES
            reasons.append(f"Fuorigioco SÌ: Efficace vs piano avversario ({adv_plan.value}).")
        else:
            offside = OffsideTrap.NO
            reasons.append("Fuorigioco NO: Assetto conservativo/standard.")

        setup_score = 1.0
        if marking == MarkingType.UOMO and offside == OffsideTrap.YES:
            setup_score -= 0.5

        return DefensiveSetup(
            marking=marking,
            offside_trap=offside,
            score=setup_score,
            reasoning=reasons
        )

def parse_marking(val: str) -> MarkingType:
    clean_val = val.strip().upper()
    if clean_val in ("ZONA", "ZONE"):
        return MarkingType.ZONA
    if clean_val in ("UOMO", "MAN"):
        return MarkingType.UOMO
    raise argparse.ArgumentTypeError(f"Marcatura '{val}' non valida. Usa 'zona' o 'uomo'.")

def parse_bool_flag(val: str) -> OffsideTrap:
    clean_val = val.strip().upper()
    if clean_val in ("SI", "SÌ", "YES", "1", "TRUE"):
        return OffsideTrap.YES
    if clean_val in ("NO", "0", "FALSE"):
        return OffsideTrap.NO
    raise argparse.ArgumentTypeError(f"Valore '{val}' non valido. Usa 'si' o 'no'.")