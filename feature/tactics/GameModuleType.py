import argparse
from enum import Enum
import re
from typing import Dict

from GameModule import GameModule
from GamePlan import GamePlan


class GameModuleType(Enum):
    """
    Enumerazione dei moduli di gioco su OSM con la loro configurazione di bilanciamento.

    Parametri per ciascuna costante:
    - code (str): Identificativo testuale del modulo.
    - defenders (int): Numero di difensori.
    - midfielders (int): Numero di centrocampisti.
    - attackers (int): Numero di attaccanti.
    - k1_optimal (float): Centro della gaussiana f_fit (forza relativa ideale in [0.0, 1.0]).
    - sigma (float): Deviazione standard (tolleranza/versatilità del modulo).
    - style_affinity (GameStyle): Stile di gioco nativo e primario per il modulo.
    """

    # --- MODULI ULTRA-DIFENSIVI / CATENACCIO (k1_opt <= 0.25) ---
    M_631A = GameModule("6-3-1A", 6, 3, 1, 0.12, 0.14, GamePlan.COUNTER_ATTACK)
    M_631B = GameModule("6-3-1B", 6, 3, 1, 0.12, 0.14, GamePlan.COUNTER_ATTACK)
    M_541A = GameModule("5-4-1A", 5, 4, 1, 0.20, 0.16, GamePlan.SHOOT_ON_SIGHT)
    M_541B = GameModule("5-4-1B", 5, 4, 1, 0.20, 0.16, GamePlan.COUNTER_ATTACK)
    M_5311 = GameModule("5-3-1-1", 5, 4, 1, 0.22, 0.16, GamePlan.COUNTER_ATTACK)
    M_532 = GameModule("5-3-2", 5, 3, 2, 0.25, 0.18, GamePlan.COUNTER_ATTACK)

    # --- MODULI DIFENSIVI E CONTROPENETRAZIONE (0.25 < k1_opt <= 0.40) ---
    M_451 = GameModule("4-5-1", 4, 5, 1, 0.30, 0.16, GamePlan.SHOOT_ON_SIGHT)
    M_523A = GameModule("5-2-3A", 5, 2, 3, 0.32, 0.15, GamePlan.COUNTER_ATTACK)
    M_523B = GameModule("5-2-3B", 5, 2, 3, 0.32, 0.15, GamePlan.COUNTER_ATTACK)
    M_4231 = GameModule("4-2-3-1", 4, 5, 1, 0.38, 0.20, GamePlan.SHOOT_ON_SIGHT)

    # --- MODULI EQUILIBRATI / FASCIA MEDIA (0.40 < k1_opt <= 0.65) ---
    M_352 = GameModule("3-5-2", 3, 5, 2, 0.48, 0.22, GamePlan.PASSING_GAME)
    M_3322 = GameModule("3-3-2-2", 3, 5, 2, 0.50, 0.20, GamePlan.PASSING_GAME)
    M_442A = GameModule("4-4-2A", 4, 4, 2, 0.55, 0.28, GamePlan.WING_PLAY)       # Alta versatilità (sigma alto)
    M_442B = GameModule("4-4-2B", 4, 4, 2, 0.58, 0.25, GamePlan.PASSING_GAME)    # Rombo centrale
    M_3232 = GameModule("3-2-3-2", 3, 5, 2, 0.62, 0.18, GamePlan.PASSING_GAME)

    # --- MODULI OFFENSIVI / DOMINANTI (0.65 < k1_opt <= 0.82) ---
    M_343A = GameModule("3-4-3A", 3, 4, 3, 0.72, 0.18, GamePlan.WING_PLAY)
    M_343B = GameModule("3-4-3B", 3, 4, 3, 0.75, 0.16, GamePlan.WING_PLAY)
    M_433B = GameModule("4-3-3B", 4, 3, 3, 0.78, 0.18, GamePlan.WING_PLAY)
    M_433A = GameModule("4-3-3A", 4, 3, 3, 0.80, 0.18, GamePlan.WING_PLAY)

    # --- MODULI HIPER-OFFENSIVI / SQUILIBRATI (k1_opt > 0.82) ---
    M_424A = GameModule("4-2-4A", 4, 2, 4, 0.85, 0.15, GamePlan.LONG_BALL)
    M_424B = GameModule("4-2-4B", 4, 2, 4, 0.85, 0.15, GamePlan.WING_PLAY)
    M_334A = GameModule("3-3-4A", 3, 3, 4, 0.88, 0.14, GamePlan.LONG_BALL)
    M_334B = GameModule("3-3-4B", 3, 3, 4, 0.88, 0.14, GamePlan.LONG_BALL)
    M_325 = GameModule("3-2-5", 3, 2, 5, 0.92, 0.12, GamePlan.LONG_BALL)


def parse_module_type(argument_value: str) -> GameModuleType:
    """
    Converte la stringa fornita da argparse nella costante GameModuleType corrispondente.

    Pulisce l'input accettando molteplici formati (es. "433A", "4-3-3A", "4_3_3_a", "433a")
    e mappa la stringa normalizzata sul valore dell'Enum.

    :param argument_value: Stringa passata da CLI tramite argparse.
    :return: Istanza corrispondente di GameModuleType.
    :raises argparse.ArgumentTypeError: Se la stringa non corrisponde a nessun modulo valido.
    """
    if not isinstance(argument_value, str):
        raise argparse.ArgumentTypeError(
            f"Expected string input, got {type(argument_value).__name__}"
        )

    # 1. Normalizzazione dell'input:
    #    - Converti in maiuscolo
    #    - Rimuovi spazi, trattini e underscore (es. "4-3-3 A" -> "433A")
    normalized_input: str = re.sub(r"[\s\-_]", "", argument_value.strip().upper())

    # 2. Mappatura dinamica delle chiavi Enum normalizzate
    #    Esempio: "M_433A" -> "433A" oppure enum.name -> "433A"
    module_lookup: Dict[str, GameModuleType] = {}
    
    for module in GameModuleType:
        # Pulisce il nome dell'Enum (es. se si chiama M_433A, 4_3_3_A, o M433A)
        clean_enum_name = re.sub(r"[\s\-_]", "", module.name.replace("M_", "").upper())
        module_lookup[clean_enum_name] = module

    # 3. Risoluzione della chiave
    if normalized_input in module_lookup:
        return module_lookup[normalized_input]

    # 4. Fallback in caso di input non valido
    valid_modules = ", ".join(sorted(module_lookup.keys()))
    raise argparse.ArgumentTypeError(
        f"Modulo tattico '{argument_value}' non valido.\n"
        f"Valori accettati: {valid_modules}"
    )