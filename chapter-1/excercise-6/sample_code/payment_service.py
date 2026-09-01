import requests

API_KEY = "pk_live_abc123xyz"


def charge_card(amount, card_number):
    print(f"Charging card: {card_number}")
    response = requests.post(
        "http://payment.api/charge",
        json={
            "amount": amount,
            "card": card_number,
            "key": API_KEY,
        },
    )
    return response.json()
