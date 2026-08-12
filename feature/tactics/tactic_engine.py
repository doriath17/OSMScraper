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

class TacticalApproach(Enum):
    MARKED_ADVANTAGE = "Vantaggio marcato"
    SLIGHT_ADVANTAGE = "Vantaggio lieve"
    BALANCED = "Equilibrio"
    SLIGHT_DISADVANTAGE = "Svantaggio lieve"
    MARKED_DISADVANTAGE = "Svantaggio marcato"

def get_effective_overall(base_overall, total_bonus):
    return base_overall * (1 + total_bonus)

def get_delta(player_base_overall, player_total_bonus, opponent_base_overall, opponent_total_bonus):
    player_effective_overall = get_effective_overall(player_base_overall, player_total_bonus)
    opponent_effective_overall = get_effective_overall(opponent_base_overall, opponent_total_bonus)
    delta = player_effective_overall - opponent_effective_overall
    return delta

def get_tactical_approach(delta):
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


## SLIDER
#
# Clamp: the clamp represents the minimum and maximum value that a function can return.
# 
# STYLE
# formula: Style(delta) = min + k * (max - min)
# - k: fattore forza relativa calcolato con un 'sigmoide' $$k = \frac{1}{1 + e^{-\lambda \cdot \Delta}}$$
#   oscilla tra 0 e 1 e indica quanto puoi permetterti di essere aggressivo o difensivo in base al delta.
# - 25 soglia minima siccome al di sotto hai uno stile di gioco troppo difensivo
# - 80 soglia massima siccome al di sopra hai uno stile di gioco troppo aggressivo
# - 50 soglia di partenza, rappresenta un bilanciamento (ricercato quando il delta è vicino a 0) tra difesa e attacco
#
# PRESSURE
# formula: Pressure(delta) = min + k * (max - min)
# NOTE: depending on the value of k, the pressure and style curves will change to be more or less steep. The lambda parameter controls the steepness of the curve, allowing for fine-tuning of the pressure and style adjustments based on the delta value.

import math

def get_k(delta: float, lambda_scale: float = 0.12) -> float:
    """
    Calcola k tramite una curva sigmoide.
    - delta: (Tuo Effective OVR) - (Adv Effective OVR)
    - lambda_scale: controlla quanto è "ripida" la transizione.
    
    Output: valore continuo tra 0.0 (netta inferiorità) e 1.0 (netto dominio).
    """
    # -lambda_scale * delta garantisce che:
    # delta = 0  => k = 0.5 (equilibrio)
    # delta > 0  => k -> 1.0 (vantaggio)
    # delta < 0  => k -> 0.0 (svantaggio)
    return 1.0 / (1.0 + math.exp(-lambda_scale * delta))

def get_style(delta: float, min_style: int = 25, max_style: int = 80) -> int:
    k = get_k(delta)    # if you need to adjust the steepness of the curve, you can modify the lambda_scale parameter in get_k
    style = min_style + k * (max_style - min_style)
    return round(style)

def get_pressure(delta: float, min_pressure: int = 25, max_pressure: int = 75) -> int:
    k = get_k(delta)    # if you need to adjust the steepness of the curve, you can modify the lambda_scale parameter in get_k
    pressure = min_pressure + k * (max_pressure - min_pressure)
    return round(pressure)

# ==============================================================================
# DOCUMENTAZIONE DEL MODELLO E SPIEGAZIONE DELLA SCELTA
# ==============================================================================
# Per il calcolo del Tempo (Velocità di Passaggio) è stato scelto l'APPROCCIO 2
# basato sulla deviazione assoluta del fattore k_1 dal punto di equilibrio (0.50).
#
# MOTIVAZIONE DELLA SCELTA:
# In OSM, sia in forte svantaggio (difesa/contropiede) sia in forte vantaggio
# (dominio/attacco di prima), serve una velocità di passaggio elevata. In fase di
# equilibrio, invece, si preferisce un ritmo medio/costruttivo per il possesso.
#
# VANTAGGI DELL'APPROCCIO 2:
# 1. COERENZA MATEMATICA: Utilizza k_1 come unica sorgente di verità condivisa
#    per tutti e 3 gli slider (Stile, Pressing, Tempo).
# 2. FLUIDITÀ SENZA IF/ELSE: Non richiede condizionali rigidi o clamping manuale,
#    sfruttando la convergenza naturale della sigmoide.
# 3. REATTIVITÀ DINAMICA: Con un esponente eta = 0.75, la risposta del ritmo è
#    immediata appena ci si allontana dallo zero, garantendo transizioni veloci.
#
# TABELLA DELL'ANDAMENTO GENERATO (con eta = 0.75, T_base = 50, T_max_diff = 40):
# ------------------------------------------------------------------------------
# Delta   | k_1    | |k_1 - 0.5| | Stile (S) | Pressing (P) | Tempo (T) | Stato
# ------------------------------------------------------------------------------
# -16.0   | 0.128  | 0.372       | 31.4      | 35.8         | 68.6      | Def. Forte
# -12.0   | 0.192  | 0.308       | 34.6      | 38.6         | 66.2      | Defensivo
#  -4.0   | 0.382  | 0.118       | 44.1      | 47.2         | 58.0      | Svant. Lieve
#   0.0   | 0.500  | 0.000       | 50.0      | 52.5         | 50.0      | Equilibrio
#  +4.0   | 0.618  | 0.118       | 55.9      | 57.8         | 58.0      | Vant. Lieve
# +12.0   | 0.808  | 0.308       | 65.4      | 66.4         | 66.2      | Offensivo
# +16.0   | 0.872  | 0.372       | 68.6      | 69.2         | 68.6      | Off. Forte
# ==============================================================================

def get_tempo(k1: float, t_base: float = 50.0, max_boost: float = 40.0, eta: float = 0.75) -> float: # Definisce il calcolo del Tempo tramite scostamento da k1.
    deviation = abs(k1 - 0.5) # Calcola la distanza assoluta tra k1 e il punto neutro 0.50.
    return round(t_base + max_boost * (deviation ** eta), 1) # Restituisce il valore del Tempo arrotondato a un decimale.

def get_all_sliders(delta: float) -> dict: # Funzione di comodo per calcolare i tre slider contemporaneamente.
    k1 = get_k(delta) # Calcola il valore dinamico k1 in base al Delta corrente.
    stile = round(25.0 + k1 * (75.0 - 25.0), 1) # Calcola lo Stile (25.0 - 75.0) in modo continuo.
    pressing = round(30.0 + k1 * (75.0 - 30.0), 1) # Calcola il Pressing (30.0 - 75.0) in modo continuo.
    tempo = get_tempo(k1) # Calcola il Tempo usando l'Approccio 2 basato su k1.
    return {"k1": round(k1, 3), "stile": stile, "pressing": pressing, "tempo": tempo} # Restituisce un dizionario contenente tutti i valori calcolati.