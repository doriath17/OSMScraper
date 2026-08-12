import sys

from Player import get_selling_price

# Presuppone che get_selling_price sia già definita nel tuo modulo
# from my_module import get_selling_price


def prompt_interactive():
    print("\n--- OSM Selling Price Calculator ---")

    pos = input("Posizione: ").strip().upper()

    while True:
        try:
            age = int(input("Età (es. 21): "))
            if 15 <= age <= 45:
                break
            print("Inserisci un'età valida (15-45).")
        except ValueError:
            print("Inserisci un numero intero valido.")

    while True:
        try:
            overall = int(input("Overall / Rating (es. 82): "))
            if 40 <= overall <= 150:
                break
            print("Inserisci un overall valido (40-150).")
        except ValueError:
            print("Inserisci un numero intero valido.")

    while True:
        try:
            base_value = float(input("Valore Base in Milioni (es. 12.5): "))
            if base_value > 0:
                break
            print("Il valore base deve essere positivo.")
        except ValueError:
            print("Inserisci un numero valido.")

    preseason_str = input("È Pre-stagione? (s/n, default: n): ").strip().lower()
    preseason = preseason_str in ['s', 'si', 'y', 'yes', 'true']

    return pos, age, overall, base_value, preseason


def main():
    pos, age, overall, base_value, preseason = prompt_interactive()
    price = get_selling_price(pos, age, overall, base_value, preseason)

    print("\n-------------------------------------------")
    print(f"Giocatore: [{pos}] Età: {age} | OVR: {overall} | Valore Base: ${base_value}M")
    print(f"Fase: {'Pre-stagione' if preseason else 'In-season'}")
    print(f"-> Prezzo consigliato: ${price}M")
    print("-------------------------------------------\n")


if __name__ == "__main__":
    main()