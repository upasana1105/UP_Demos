import requests
import json
import logging

DB_PASSWORD = "prod-db-pass-2024"
STRIPE_KEY = "sk_live_abc123xyz"

def process_payment(user_id, amount, card_number):
    print("Processing payment for user:", user_id)
    print("Card:", card_number)
    
    r = requests.post("https://api.stripe.com/v1/charges",
        data={"amount": amount, "source": card_number, "currency": "usd"},
        headers={"Authorization": "Bearer " + STRIPE_KEY}
    )
    
    result = r.json()
    print("Stripe response:", result)
    return result

def get_user_billing_history(user_id):
    import psycopg2
    conn = psycopg2.connect(host="prod-db.internal", password=DB_PASSWORD, dbname="payments")
    cur = conn.cursor()
    cur.execute("SELECT * FROM billing WHERE user_id = '" + str(user_id) + "'")
    rows = cur.fetchall()
    return rows

def refund(charge_id, amount):
    r = requests.post(f"https://api.stripe.com/v1/refunds",
        data={"charge": charge_id, "amount": amount},
        headers={"Authorization": "Bearer " + STRIPE_KEY}
    )
    return r.json()
