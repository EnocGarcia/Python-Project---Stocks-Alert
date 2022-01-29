"""Stocks Alert Project"""
import os
import datetime as dt
import requests
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

STOCKS_ENDPOINT = "https://www.alphavantage.co/query?"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything?"
STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc."
DAYS_HISTORY = 2

current_date = dt.datetime.now().date()

stocks_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "output": "compact",
    "apikey": os.environ.get("STOCKS_API_KEY"),
}

news_parameters = {
    "apiKey": os.environ.get("NEWS_API_KEY"),
    "q": COMPANY_NAME,
    "from": f"{current_date - dt.timedelta(days=DAYS_HISTORY)}",
}

stocks_response = requests.get(STOCKS_ENDPOINT, stocks_parameters)
stocks_response.raise_for_status()

stocks_md = stocks_response.json()["Meta Data"]

last_date = map(int, stocks_md["3. Last Refreshed"].split("-"))
last_date = dt.datetime(
    *last_date, tzinfo=None
).date()  # tzinfo is just to avoid pylint error
day_before = last_date - dt.timedelta(days=1)

stocks_fulldata = stocks_response.json()["Time Series (Daily)"]
delta_data = {
    k: v
    for (k, v) in stocks_fulldata.items()
    if (k in [str(last_date), str(day_before)])
}

opening_values = (
    float(delta_data[str(last_date)]["1. open"]),
    float(delta_data[str(day_before)]["1. open"]),
)

closing_values = (
    float(delta_data[str(last_date)]["4. close"]),
    float(delta_data[str(day_before)]["4. close"]),
)

delta = lambda x, y: ((x - y) / y) * 100

if abs(delta(*opening_values)) > 5 or abs(delta(*closing_values)):
    news_response = requests.get(NEWS_ENDPOINT, news_parameters)
    news_response.raise_for_status()

    articles_data = news_response.json()["articles"][:3]
    last_articles = [(article["title"], article["url"]) for article in articles_data]
    message_body = f"{COMPANY_NAME} Stock Alert.\n"
    for article in last_articles:
        message_body += f"Headline: {article[0]}\nurl: {article[1]}\n"

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    sender = os.environ.get("SENDER_PHONE_NUMBER")
    receiver = os.environ.get("RECEIVER_PHONE_NUMBER")

    client = Client(account_sid, auth_token)
    message = client.messages.create(from_=sender, to=receiver, body=message_body)
