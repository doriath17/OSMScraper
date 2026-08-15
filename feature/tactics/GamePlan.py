import argparse
from enum import Enum
import re
from typing import Dict


class GamePlan(Enum):
    """
    Enumerazione degli stili di gioco (tattiche di costruzione) su OSM.

    Definisce la modalità nativa con cui la squadra sviluppa la manovra offensiva
    e transita la palla dalla difesa all'attacco. Ogni stile impone precisi 
    vincoli sul posizionamento dei reparti e influenza la taratura dello slider Tempo.

    Valori:
    - WING_PLAY: Sviluppo sulle corsie esterne con sovrapposizioni e cross.
    - PASSING_GAME: Trama centrale basata sul possesso palla e passaggi corti (Tiki-Taka).
    - SHOOT_ON_SIGHT: Conclusione rapida dalla media/lunga distanza da parte dei centrocampisti.
    - COUNTER_ATTACK: Transizione verticale immediata dopo il recupero palla in zona bassa.
    - LONG_BALL: Lancio diretto dalla linea difensiva per scavalcare il centrocampo.
    """

    WING_PLAY = ("wing play", (60, 80), 1.05)
    PASSING_GAME = ("passing game", (50, 70), 0.90)
    SHOOT_ON_SIGHT = ("shoot on sight", (30, 50), 1.00)
    COUNTER_ATTACK = ("counter attack", (20, 45), 1.20)
    LONG_BALL = ("long ball", (40, 65), 1.25)

    def __init__(self, value_name: str, preferred_mentality_range: tuple[int, int], tempo_multiplier: float):
        self.value_name = value_name
        self.preferred_mentality_range = preferred_mentality_range
        self.tempo_multiplier = tempo_multiplier

def parse_game_plan(argument_value: str) -> GamePlan:
    """
    Converte la stringa fornita da argparse nell'Enum GamePlan corrispondente.

    Normalizza l'input e supporta sia i nomi degli Enum che alias italiani/inglesi comuni
    (es. "wing-play", "fasce", "tiki-taka", "tikitaka", "counter", "contropiede").

    :param argument_value: Stringa passata da CLI tramite argparse.
    :return: Istanza corrispondente di GamePlan.
    :raises argparse.ArgumentTypeError: Se la stringa non corrisponde a nessun piano valido.
    """
    if not isinstance(argument_value, str):
        raise argparse.ArgumentTypeError(
            f"Expected string input, got {type(argument_value).__name__}"
        )

    # 1. Normalizzazione dell'input: maiuscolo, rimozione di spazi, trattini e underscore
    normalized_input: str = re.sub(r"[\s\-_]", "", argument_value.strip().upper())

    # 2. Mappatura degli alias per una CLI flessibile
    # Mappa le varianti testuali normalizzate verso i valori dell'Enum GamePlan
    plan_lookup: Dict[str, GamePlan] = {
        # Alias per WING_PLAY
        "WINGPLAY": GamePlan.WING_PLAY,
        "WING": GamePlan.WING_PLAY,
        "FASCE": GamePlan.WING_PLAY,
        "GIOCOSULLEFASCE": GamePlan.WING_PLAY,

        # Alias per TIKI_TAKA
        "TIKITAKA": GamePlan.PASSING_GAME,
        "TIKI": GamePlan.PASSING_GAME,
        "POSSESSO": GamePlan.PASSING_GAME,
        "PASSINGGAME": GamePlan.PASSING_GAME,

        # Alias per COUNTER_ATTACK
        "COUNTERATTACK": GamePlan.COUNTER_ATTACK,
        "COUNTER": GamePlan.COUNTER_ATTACK,
        "CONTROPIEDE": GamePlan.COUNTER_ATTACK,

        # Alias per SHOOT_ON_SIGHT
        "SHOOTONSIGHT": GamePlan.SHOOT_ON_SIGHT,
        "SHOOT": GamePlan.SHOOT_ON_SIGHT,
        "TIRA": GamePlan.SHOOT_ON_SIGHT,
        "TIRADAOGNIPOSIZIONE": GamePlan.SHOOT_ON_SIGHT,

        # Alias per LONG_BALL
        "LONGBALL": GamePlan.LONG_BALL,
        "PALLALUNGA": GamePlan.LONG_BALL,
        "LANCIO": GamePlan.LONG_BALL,
    }

    # 3. Registrazione dinamica diretta dei nomi degli Enum (fallback)
    for plan in GamePlan:
        clean_enum_name = re.sub(r"[\s\-_]", "", plan.name.upper())
        plan_lookup.setdefault(clean_enum_name, plan)

    # 4. Risoluzione dell'input
    if normalized_input in plan_lookup:
        return plan_lookup[normalized_input]

    # 5. Gestione errore
    valid_inputs = ", ".join(sorted(set(plan_lookup.keys())))
    raise argparse.ArgumentTypeError(
        f"Game plan '{argument_value}' non valido.\n"
        f"Valori/alias accettati: {valid_inputs}"
    )