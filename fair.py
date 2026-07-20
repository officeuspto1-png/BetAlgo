import hashlib
import secrets
import time

class ProvablyFair:
    """Provably fair algorithm implementation"""
    
    @staticmethod
    def generate_seed():
        """Generate a secure random seed"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_seed(seed):
        """Hash a seed for verification"""
        return hashlib.sha256(seed.encode()).hexdigest()
    
    @staticmethod
    def combine_seeds(server_seed, client_seed, nonce):
        """Combine server and client seeds"""
        combined = f"{server_seed}-{client_seed}-{nonce}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    @staticmethod
    def generate_random(hash_result, max_value):
        """Generate random number from hash"""
        # Convert hash to integer
        int_value = int(hash_result[:16], 16)
        return int_value % max_value
    
    @staticmethod
    def generate_outcome(server_seed, client_seed, nonce, game_type):
        """Generate provably fair outcome for any game"""
        combined_hash = ProvablyFair.combine_seeds(server_seed, client_seed, nonce)
        
        if game_type == 'coinflip':
            # 0 = Heads, 1 = Tails
            result = ProvablyFair.generate_random(combined_hash, 2)
            return 'Heads' if result == 0 else 'Tails'
        
        elif game_type == 'dice':
            # 1-100
            return ProvablyFair.generate_random(combined_hash, 100) + 1
        
        elif game_type == 'roulette':
            # 0-36 (European Roulette)
            return ProvablyFair.generate_random(combined_hash, 37)
        
        elif game_type == 'crash':
            # 1.00x - 1000x
            value = ProvablyFair.generate_random(combined_hash, 100000) / 100
            return max(1.00, value)
        
        return None
    
    @staticmethod
    def verify_game(server_seed, client_seed, nonce, game_type, actual_outcome):
        """Verify a game outcome"""
        combined_hash = ProvablyFair.combine_seeds(server_seed, client_seed, nonce)
        calculated = ProvablyFair.generate_outcome(server_seed, client_seed, nonce, game_type)
        return calculated == actual_outcome
    
    @staticmethod
    def get_verification_message(server_seed, client_seed, nonce, game_type, outcome):
        """Generate verification message for user"""
        combined_hash = ProvablyFair.combine_seeds(server_seed, client_seed, nonce)
        
        message = f"""
🔐 *PROVABLY FAIR VERIFICATION*

📋 *Game Details:*
• Game: {game_type.capitalize()}
• Outcome: {outcome}
• Nonce: {nonce}

🔑 *Seeds:*
• Server Seed: `{server_seed}`
• Client Seed: `{client_seed}`

🔗 *Verification Data:*
• Combined Hash: `{combined_hash[:16]}...`

📝 *How to Verify:*
1. Save the seeds and nonce
2. Use any SHA256 hashing tool
3. Hash: `{server_seed}-{client_seed}-{nonce}`
4. Compare with the game result

✅ *This game is 100% verifiable!*
"""
        return message
