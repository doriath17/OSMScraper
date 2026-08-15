import argparse
from enum import Enum
import re
from typing import Dict, Optional, Tuple

from GameModuleType import GameModuleType
from GamePlan import GamePlan
from GameDefense import MarkingType, OffsideTrap

class GamePlanSelector:
    """
    Selettore e valutatore del GamePlan ottimale basato sull'interazione tra:
    - Affinità con il proprio modulo (M*)
    - Vulnerabilità del modulo avversario (M_adv)
    - Contromossa al GamePlan avversario (P_adv, se noto)
    - Forza relativa (k)
    """

    # Matrice di affinità Modulo-GamePlan (Default: 0.5 per combinazioni non specificate)
    AFFINITY_MATRIX: Dict[Tuple[GameModuleType, GamePlan], float] = {
        # 4-3-3 A/B preferiscono nettamente le fasce o il Tiki-Taka
        (GameModuleType.M_433A, GamePlan.WING_PLAY): 1.0,
        (GameModuleType.M_433A, GamePlan.PASSING_GAME): 0.8,
        (GameModuleType.M_433B, GamePlan.WING_PLAY): 1.0,
        (GameModuleType.M_433B, GamePlan.PASSING_GAME): 0.8,
        # 4-4-2 A/B
        (GameModuleType.M_442A, GamePlan.WING_PLAY): 0.9,
        (GameModuleType.M_442A, GamePlan.PASSING_GAME): 0.7,
        (GameModuleType.M_442B, GamePlan.PASSING_GAME): 0.9,
        # Moduli difensivi / da contropiede (5-3-2, 5-4-1, 4-5-1)
        (GameModuleType.M_532, GamePlan.COUNTER_ATTACK): 1.0,
        (GameModuleType.M_532, GamePlan.LONG_BALL): 0.8,
        (GameModuleType.M_451, GamePlan.SHOOT_ON_SIGHT): 1.0,
        (GameModuleType.M_451, GamePlan.COUNTER_ATTACK): 0.8,
    }

    @staticmethod
    def get_affinity(module: GameModuleType, plan: GamePlan) -> float:
        """Ritorna l'affinità strutturale tra un modulo e un piano di gioco [0.0, 1.0]."""
        return GamePlanSelector.AFFINITY_MATRIX.get((module, plan), 0.5)

    @staticmethod
    def get_structural_advantage(plan: GamePlan, adv_module: GameModuleType) -> float:
        """
        Valuta quanto il piano di gioco sfrutta le debolezze geometriche di M_adv.
        """
        adv_defenders = adv_module.value.defenders
        adv_midfielders = adv_module.value.midfielders

        # Difesa a 3 o moduli stretti -> soffrono il Gioco sulle Fasce
        if adv_defenders <= 3 and plan == GamePlan.WING_PLAY:
            return 1.0

        # Centrocampo poco denso (<= 3) -> soffre il dominio del pallone (Passing Game)
        if adv_midfielders <= 3 and plan == GamePlan.PASSING_GAME:
            return 0.9

        # Difese molto folte (>= 5) -> difficili da penetrare, vulnerabili al tiro da fuori
        if adv_defenders >= 5 and plan == GamePlan.SHOOT_ON_SIGHT:
            return 0.9

        # Moduli iper-offensivi -> lasciano campo al Contropiede
        if adv_defenders <= 3 and adv_midfielders <= 3 and plan == GamePlan.COUNTER_ATTACK:
            return 1.0

        return 0.4  # Valore neutro/base

    @staticmethod
    def get_counter_plan_score(plan: GamePlan, adv_plan: Optional[GamePlan]) -> float:
        """
        Calcola la contromossa tattica contro il GamePlan avversario (se disponibile).
        """
        if adv_plan is None:
            return 0.0  # Nessun impatto se l'informazione è ignota

        # Matrice delle contromosse ottimali
        COUNTER_MAP = {
            GamePlan.WING_PLAY: [GamePlan.PASSING_GAME, GamePlan.COUNTER_ATTACK],
            GamePlan.PASSING_GAME: [GamePlan.SHOOT_ON_SIGHT, GamePlan.COUNTER_ATTACK],
            GamePlan.COUNTER_ATTACK: [GamePlan.WING_PLAY, GamePlan.SHOOT_ON_SIGHT],
            GamePlan.SHOOT_ON_SIGHT: [GamePlan.WING_PLAY, GamePlan.PASSING_GAME],
            GamePlan.LONG_BALL: [GamePlan.PASSING_GAME, GamePlan.WING_PLAY],
        }

        best_counters = COUNTER_MAP.get(adv_plan, [])
        if plan in best_counters:
            return 1.0
        elif plan == adv_plan:
            return 0.5  # Scontro speculare
        else:
            return 0.2  # Sub-ottimale

    @staticmethod
    def get_context_score(plan: GamePlan, k: float) -> float:
        """
        Valuta l'adeguatezza del piano di gioco in base alla forza relativa k.
        """
        # In forte svantaggio k < 0.35: premiamo stili speculativi
        if k < 0.35:
            if plan in (GamePlan.COUNTER_ATTACK, GamePlan.LONG_BALL, GamePlan.SHOOT_ON_SIGHT):
                return 1.0
            elif plan == GamePlan.PASSING_GAME:
                return 0.1  # Pericoloso palleggiare se inferiori

        # In forte dominio k > 0.65: premiamo stili di possesso e attacco
        elif k > 0.65:
            if plan in (GamePlan.WING_PLAY, GamePlan.PASSING_GAME, GamePlan.SHOOT_ON_SIGHT):
                return 1.0
            elif plan == GamePlan.COUNTER_ATTACK:
                return 0.2  # Inefficace se l'avversario si difende basso

        return 0.6  # Valore neutro per situazioni equilibrate

    @classmethod
    def evaluate_pair(
        cls,
        module: GameModuleType,
        plan: GamePlan,
        k: float,
        adv_module: GameModuleType,
        adv_plan: Optional[GamePlan] = None,
        adv_marking: Optional[MarkingType] = None,
        adv_offside: Optional[OffsideTrap] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calcola lo score complessivo per la combinazione (Modulo, GamePlan),
        inclusa la valutazione contro la difesa avversaria (marcatura e fuorigioco).
        """
        has_adv_plan = adv_plan is not None
        has_adv_def = (adv_marking is not None) or (adv_offside is not None)

        if weights is None:
            # Bilanciamento dinamico dei pesi in base ai dati disponibili
            if has_adv_plan and has_adv_def:
                weights = {"affinity": 0.25, "structural": 0.25, "counter": 0.20, "def_counter": 0.15, "context": 0.15}
            elif has_adv_plan:
                weights = {"affinity": 0.30, "structural": 0.30, "counter": 0.25, "def_counter": 0.00, "context": 0.15}
            elif has_adv_def:
                weights = {"affinity": 0.30, "structural": 0.30, "counter": 0.00, "def_counter": 0.25, "context": 0.15}
            else:
                weights = {"affinity": 0.35, "structural": 0.35, "counter": 0.00, "def_counter": 0.00, "context": 0.30}

        s_aff = cls.get_affinity(module, plan)
        s_struct = cls.get_structural_advantage(plan, adv_module)
        s_counter = cls.get_counter_plan_score(plan, adv_plan)
        s_def_counter = cls.get_counter_defensive_setup_score(plan, adv_marking, adv_offside)
        s_context = cls.get_context_score(plan, k)

        total_score = (
            weights["affinity"] * s_aff +
            weights["structural"] * s_struct +
            weights["counter"] * s_counter +
            weights["def_counter"] * s_def_counter +
            weights["context"] * s_context
        )

        breakdown = {
            "affinity_score": round(s_aff, 3),
            "structural_score": round(s_struct, 3),
            "counter_score": round(s_counter, 3),
            "def_counter_score": round(s_def_counter, 3),
            "context_score": round(s_context, 3),
        }

        return round(total_score, 4), breakdown

    @staticmethod
    def get_counter_defensive_setup_score(
        plan: GamePlan, 
        adv_marking: Optional[MarkingType], 
        adv_offside: Optional[OffsideTrap]
    ) -> float:
        """Calcola il bonus/malus del piano di gioco contro la difesa avversaria."""
        score = 0.5  # Neutro se ignoti

        # Vs Fuorigioco SÌ -> Favorisci verticalizzazioni e ripartenze
        if adv_offside == OffsideTrap.YES:
            if plan in (GamePlan.COUNTER_ATTACK, GamePlan.LONG_BALL):
                score += 0.3
            elif plan == GamePlan.PASSING_GAME:
                score -= 0.2

        # Vs Marcatura a Uomo -> Favorisci l'ampiezza e il fraseggio
        if adv_marking == MarkingType.UOMO:
            if plan in (GamePlan.WING_PLAY, GamePlan.PASSING_GAME):
                score += 0.2
            elif plan == GamePlan.SHOOT_ON_SIGHT:
                score -= 0.1

        return max(0.0, min(1.0, score))


