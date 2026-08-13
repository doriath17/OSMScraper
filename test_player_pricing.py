import pytest

from Player import Player

@pytest.mark.parametrize(
    "player_data, budget, operative_budget, matchday, expected_price_min, expected_price_max, min_score",
    [
        # Scenario 1: Giovane Top, Cassa Alta -> ~21.2M
        (
            {"name": "Giovane Top", "position": "ST", "age": 19, "nationality": "ITA", "club": "Club A", "attack": 88, "defense": 30, "overall": 88, "main_stat": 88, "market_value": 12.0, "base_value": 10.0},
            50.0, 15.0, 5,
            21.0, 22.0, 0.1
        ),
        # Scenario 2: Giovane Top, Cassa Bassa -> Prezzo ridotto (~20.7M)
        (
            {"name": "Giovane Top", "position": "ST", "age": 19, "nationality": "ITA", "club": "Club A", "attack": 88, "defense": 30, "overall": 88, "main_stat": 88, "market_value": 12.0, "base_value": 10.0},
            5.0, 2.5, 5,
            20.0, 21.0, 0.01
        ),
        # Scenario 3: Veterano, Cassa Media -> ~12.9M
        (
            {"name": "Veterano", "position": "CM", "age": 33, "nationality": "ITA", "club": "Club B", "attack": 80, "defense": 80, "overall": 80, "main_stat": 80, "market_value": 8.0, "base_value": 7.0},
            20.0, 8.0, 15,
            12.0, 13.5, 0.01
        ),
        # Scenario 4: Flop Inizio Stagione -> ~9.7M
        (
            {"name": "Medio Inizio", "position": "CB", "age": 26, "nationality": "ITA", "club": "Club C", "attack": 20, "defense": 75, "overall": 75, "main_stat": 75, "market_value": 5.0, "base_value": 5.0},
            30.0, 10.0, 2,
            9.0, 10.5, 0.1
        ),
        # Scenario 5: Urgenza Fine Stagione -> ~9.4M
        (
            {"name": "Medio Fine", "position": "CB", "age": 26, "nationality": "ITA", "club": "Club C", "attack": 20, "defense": 75, "overall": 75, "main_stat": 75, "market_value": 5.0, "base_value": 5.0},
            30.0, 10.0, 32,
            8.5, 9.8, 0.1
        ),
    ]
)

def test_selling_price_scenarios(
    player_data, budget, operative_budget, matchday, expected_price_min, expected_price_max, min_score
):
    player = Player(**player_data)
    result = player.selling_price(budget=budget, operative_budget=operative_budget, matchday=matchday)

    # Verifiche sulla struttura del dizionario restituito
    assert "price" in result, "Il dizionario deve contenere la chiave 'price'"
    assert "score" in result, "Il dizionario deve contenere la chiave 'score'"

    # Verifica che il prezzo ottimizzato rientri nel range atteso dallo scenario
    assert expected_price_min <= result["price"] <= expected_price_max, (
        f"Prezzo calcolato ({result['price']}) fuori dal range atteso "
        f"[{expected_price_min}, {expected_price_max}] per {player.name}"
    )

    # Verifica che lo score sia valido e positivo
    assert result["score"] >= min_score, (
        f"Score calcolato ({result['score']}) inferiore al minimo atteso ({min_score})"
    )


def test_budget_impact_comparison():
    """Test comparativo per verificare che a parità di giocatore una cassa più bassa produca un prezzo inferiore o uguale."""
    player_data = {
        "name": "Test Player", "position": "ST", "age": 19, "nationality": "ITA",
        "club": "Club A", "attack": 88, "defense": 30, "overall": 88,
        "main_stat": 88, "market_value": 12.0, "base_value": 10.0
    }
    
    player = Player(**player_data)

    res_high_budget = player.selling_price(budget=50.0, operative_budget=15.0, matchday=5)
    res_low_budget = player.selling_price(budget=5.0, operative_budget=2.5, matchday=5)

    # Il prezzo con cassa bassa deve essere minore per favorire una vendita rapida
    assert res_low_budget["price"] < res_high_budget["price"], (
        f"Il prezzo a cassa bassa ({res_low_budget['price']}) "
        f"dovrebbe essere inferiore a quello a cassa alta ({res_high_budget['price']})"
    )