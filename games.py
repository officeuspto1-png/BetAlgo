import random
import secrets
from fair import ProvablyFair
from config import Config

class BetAlgoGames:
    """Game logic for BetAlgo"""
    
    def __init__(self):
        self.house_edge = Config.HOUSE_EDGE
    
    def coinflip(self, bet, choice, client_seed):
        """Coinflip game"""
        server_seed = ProvablyFair.generate_seed()
        nonce = secrets.randbits(32)
        
        # Generate fair outcome
        result = ProvablyFair.generate_outcome(server_seed, client_seed, nonce, 'coinflip')
        
        # Calculate result
        win = result == choice
        win_amount = bet * 2 if win else -bet
        
        # Apply house edge for wins
        if win:
            win_amount = win_amount * (1 - self.house_edge)
        
        return {
            'result': result,
            'win': win,
            'win_amount': round(win_amount, 2),
            'server_seed': server_seed,
            'client_seed': client_seed,
            'nonce': nonce,
            'game_type': 'coinflip'
        }
    
    def dice(self, bet, target, over_under, client_seed):
        """Dice game"""
        server_seed = ProvablyFair.generate_seed()
        nonce = secrets.randbits(32)
        
        # Generate fair outcome
        roll = ProvablyFair.generate_outcome(server_seed, client_seed, nonce, 'dice')
        
        # Determine win/loss
        if over_under == 'over':
            win = roll > target
        else:
            win = roll < target
        
        # Calculate win amount
        if win:
            # 1% house edge
            odds = 100 / (100 - target) if over_under == 'under' else 100 / target
            win_amount = bet * odds
            win_amount = win_amount * (1 - self.house_edge)
        else:
            win_amount = -bet
        
        return {
            'result': roll,
            'win': win,
            'win_amount': round(win_amount, 2),
            'target': target,
            'server_seed': server_seed,
            'client_seed': client_seed,
            'nonce': nonce,
            'game_type': 'dice'
        }
    
    def roulette(self, bet, bet_type, number, client_seed):
        """Roulette game"""
        server_seed = ProvablyFair.generate_seed()
        nonce = secrets.randbits(32)
        
        # Generate fair outcome
        result = ProvablyFair.generate_outcome(server_seed, client_seed, nonce, 'roulette')
        
        # Determine win/loss
        win = False
        win_multiplier = 0
        
        if bet_type == 'number':
            win = result == number
            win_multiplier = 35 if win else 0
        elif bet_type == 'red':
            reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
            win = result in reds and result != 0
            win_multiplier = 2 if win else 0
        elif bet_type == 'black':
            blacks = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
            win = result in blacks and result != 0
            win_multiplier = 2 if win else 0
        elif bet_type == 'even':
            win = result % 2 == 0 and result != 0
            win_multiplier = 2 if win else 0
        elif bet_type == 'odd':
            win = result % 2 == 1 and result != 0
            win_multiplier = 2 if win else 0
        
        # Calculate win amount
        if win:
            win_amount = bet * win_multiplier
            win_amount = win_amount * (1 - self.house_edge)
        else:
            win_amount = -bet
        
        return {
            'result': result,
            'win': win,
            'win_amount': round(win_amount, 2),
            'server_seed': server_seed,
            'client_seed': client_seed,
            'nonce': nonce,
            'game_type': 'roulette',
            'bet_type': bet_type
        }
    
    def crash(self, bet, target, client_seed):
        """Crash game"""
        server_seed = ProvablyFair.generate_seed()
        nonce = secrets.randbits(32)
        
        # Generate fair outcome
        crash_point = ProvablyFair.generate_outcome(server_seed, client_seed, nonce, 'crash')
        
        # Determine win/loss
        win = target <= crash_point
        
        if win:
            win_amount = bet * target
            win_amount = win_amount * (1 - self.house_edge)
        else:
            win_amount = -bet
        
        return {
            'result': crash_point,
            'win': win,
            'win_amount': round(win_amount, 2),
            'target': target,
            'server_seed': server_seed,
            'client_seed': client_seed,
            'nonce': nonce,
            'game_type': 'crash'
        }
