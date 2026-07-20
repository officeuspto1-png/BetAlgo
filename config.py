import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """BetAlgo Configuration"""
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found")
    
    # Game Settings
    HOUSE_EDGE = 0.02  # 2% house edge
    MIN_BET = 1
    MAX_BET = 1000
    STARTING_BALANCE = 100
    
    # Game Limits
    MAX_COINFLIP = 500
    MAX_DICE = 100
    MAX_ROULETTE = 500
    MAX_CRASH = 200
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///betalgo.db')
