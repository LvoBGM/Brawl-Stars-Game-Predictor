import requests
from typing import Literal, List
import csv
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
CSV_FILE = "data.csv"

PLAYER_DATA_COUNT = 10
MATCHES_PER_PLAYER = 3

def main():
    ...


if __name__ == "__main__":
    main()