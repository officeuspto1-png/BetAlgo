#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import secrets
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

from config import Config
from database import Database
from games import BetAlgoGames
from fair import ProvablyFair

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== CONSTANTS ====================
SELECTING_GAME, BET_AMOUNT, GAME_CHOICE, CLIENT_SEED = range(4)

# ==================== INITIALIZATION ====================
db = Database()
games = BetAlgoGames()

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    db_user = db.get_user(user.id)
    
    keyboard = [
        [InlineKeyboardButton("🎯 Coinflip", callback_data="game_coinflip"),
         InlineKeyboardButton("🎲 Dice", callback_data="game_dice")],
        [InlineKeyboardButton("🎡 Roulette", callback_data="game_roulette"),
         InlineKeyboardButton("💥 Crash", callback_data="game_crash")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("🔐 Verify", callback_data="verify")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"""
🎰 *BETALGO* - Provably Fair Gaming 🎰

*Welcome {user.first_name}!*

💰 Balance: ${db_user.balance:.2f}
🎮 Games Played: {db_user.games_played}
🏆 Games Won: {db_user.games_won}

*Select a game to play:*
""",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check balance"""
    user = update.effective_user
    db_user = db.get_user(user.id)
    
    await update.message.reply_text(
        f"""
💰 *Balance*
━━━━━━━━━━━━
💵 Balance: ${db_user.balance:.2f}
🎮 Games: {db_user.games_played}
🏆 Wins: {db_user.games_won}

*Type /start to play!*
""",
        parse_mode='Markdown'
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stats"""
    user = update.effective_user
    db_user = db.get_user(user.id)
    
    win_rate = (db_user.games_won / db_user.games_played * 100) if db_user.games_played > 0 else 0
    
    await update.message.reply_text(
        f"""
📊 *Your Stats*
━━━━━━━━━━━━
🎮 Games Played: {db_user.games_played}
🏆 Games Won: {db_user.games_won}
📈 Win Rate: {win_rate:.1f}%
💰 Total Bet: ${db_user.total_bet:.2f}
💵 Total Win: ${db_user.total_win:.2f}
💎 Balance: ${db_user.balance:.2f}

*Keep playing!*
""",
        parse_mode='Markdown'
    )

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verify fairness"""
    await update.message.reply_text(
        """
🔐 *Provably Fair Verification*

All games use SHA256 hashing for fairness.

*How it works:*
1. Server seed is generated (hashed)
2. You provide client seed
3. Game outcome is determined
4. You can verify after the game

*To verify your last game:*
1. Save the game nonce
2. Use the server and client seeds
3. Hash: `server-client-nonce`
4. Compare with game result

*Type /start to play!*
""",
        parse_mode='Markdown'
    )

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "balance":
        user = update.effective_user
        db_user = db.get_user(user.id)
        await query.edit_message_text(
            f"💰 *Balance:* ${db_user.balance:.2f}\n\nType /start to play!",
            parse_mode='Markdown'
        )
        return
    
    if data == "stats":
        user = update.effective_user
        db_user = db.get_user(user.id)
        win_rate = (db_user.games_won / db_user.games_played * 100) if db_user.games_played > 0 else 0
        await query.edit_message_text(
            f"""
📊 *Your Stats*
━━━━━━━━━━━━
🎮 Games: {db_user.games_played}
🏆 Wins: {db_user.games_won}
📈 Win Rate: {win_rate:.1f}%
💰 Balance: ${db_user.balance:.2f}
""",
            parse_mode='Markdown'
        )
        return
    
    if data == "verify":
        await query.edit_message_text(
            """
🔐 *Provably Fair Verification*

All games use SHA256 hashing for fairness.

*To verify any game:*
1. Get server seed, client seed, and nonce
2. Hash: `server-client-nonce`
3. Compare with game result

*Every game result is verifiable!*
""",
            parse_mode='Markdown'
        )
        return
    
    # Game selection
    if data.startswith("game_"):
        game = data.replace("game_", "")
        context.user_data['selected_game'] = game
        
        # Generate initial client seed
        context.user_data['client_seed'] = secrets.token_hex(16)
        
        await query.edit_message_text(
            f"""
🎯 *{game.capitalize()}*

💰 Balance: ${db.get_user(update.effective_user.id).balance:.2f}

*Enter your bet amount:*
(MIN: ${Config.MIN_BET} - MAX: ${Config.MAX_BET})

Or type /cancel to cancel.
""",
            parse_mode='Markdown'
        )
        return BET_AMOUNT

async def handle_bet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bet amount input"""
    try:
        bet = float(update.message.text)
        
        if bet < Config.MIN_BET or bet > Config.MAX_BET:
            await update.message.reply_text(
                f"❌ Invalid bet amount. Min: ${Config.MIN_BET} - Max: ${Config.MAX_BET}",
                parse_mode='Markdown'
            )
            return BET_AMOUNT
        
        # Check balance
        user = update.effective_user
        db_user = db.get_user(user.id)
        
        if bet > db_user.balance:
            await update.message.reply_text(
                f"❌ Insufficient balance! You have ${db_user.balance:.2f}",
                parse_mode='Markdown'
            )
            return BET_AMOUNT
        
        context.user_data['bet_amount'] = bet
        game = context.user_data.get('selected_game')
        
        # Game-specific prompts
        if game == 'coinflip':
            keyboard = [
                [InlineKeyboardButton("🪙 Heads", callback_data="coinflip_heads"),
                 InlineKeyboardButton("🪙 Tails", callback_data="coinflip_tails")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"🎯 *Coinflip* | Bet: ${bet:.2f}\n\nChoose your side:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return GAME_CHOICE
        
        elif game == 'dice':
            await update.message.reply_text(
                f"🎲 *Dice* | Bet: ${bet:.2f}\n\n"
                "Send target number (1-99):\n"
                "Then send 'over' or 'under'",
                parse_mode='Markdown'
            )
            return GAME_CHOICE
        
        elif game == 'roulette':
            await update.message.reply_text(
                f"🎡 *Roulette* | Bet: ${bet:.2f}\n\n"
                "Choose type:\n"
                "Send: `number 7` - Pick a number\n"
                "Send: `red` - Bet on red\n"
                "Send: `black` - Bet on black\n"
                "Send: `even` - Bet on even\n"
                "Send: `odd` - Bet on odd",
                parse_mode='Markdown'
            )
            return GAME_CHOICE
        
        elif game == 'crash':
            await update.message.reply_text(
                f"💥 *Crash* | Bet: ${bet:.2f}\n\n"
                "Enter target multiplier (1.01 - 100.00):",
                parse_mode='Markdown'
            )
            return GAME_CHOICE
    
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number.",
            parse_mode='Markdown'
        )
        return BET_AMOUNT

async def handle_game_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game choices"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    bet = context.user_data.get('bet_amount', 0)
    client_seed = context.user_data.get('client_seed', secrets.token_hex(16))
    
    if query.data.startswith("coinflip_"):
        choice = query.data.replace("coinflip_", "").capitalize()
        
        # Play game
        result = games.coinflip(bet, choice, client_seed)
        
        # Update balance
        db.update_balance(user.id, result['win_amount'])
        db.save_game(
            user.id, 'coinflip', bet, 
            result['result'], result['win_amount'],
            result['server_seed'], result['client_seed'], result['nonce']
        )
        
        # Show result
        emoji = '✅' if result['win'] else '❌'
        keyboard = [[InlineKeyboardButton("🔄 Play Again", callback_data=f"game_coinflip")],
                    [InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"""
{emoji} *Coinflip Result*

Your choice: {choice}
Result: {result['result']}
{'🎉 YOU WIN!' if result['win'] else '😢 YOU LOSE'}

💰 Change: ${result['win_amount']:.2f}
💵 New Balance: ${db.get_user(user.id).balance:.2f}
🔑 Nonce: {result['nonce']}

🔐 *Provably Fair*
Server Seed: `{result['server_seed']}`
Client Seed: `{result['client_seed']}`

*Verify: SHA256({result['server_seed']}-{result['client_seed']}-{result['nonce']})*
""",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def handle_text_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text-based game choices"""
    text = update.message.text.lower()
    user = update.effective_user
    bet = context.user_data.get('bet_amount', 0)
    client_seed = context.user_data.get('client_seed', secrets.token_hex(16))
    game = context.user_data.get('selected_game')
    
    if game == 'dice':
        try:
            # Parse target and direction
            parts = text.split()
            if len(parts) >= 2:
                target = int(parts[0])
                direction = parts[1]
            else:
                target = int(text)
                direction = 'over'  # default
            
            if target < 1 or target > 99:
                await update.message.reply_text(
                    "❌ Target must be between 1 and 99.",
                    parse_mode='Markdown'
                )
                return GAME_CHOICE
            
            if direction not in ['over', 'under']:
                await update.message.reply_text(
                    "❌ Use 'over' or 'under'",
                    parse_mode='Markdown'
                )
                return GAME_CHOICE
            
            # Play game
            result = games.dice(bet, target, direction, client_seed)
            
            # Update balance
            db.update_balance(user.id, result['win_amount'])
            db.save_game(
                user.id, 'dice', bet,
                f"Rolled {result['result']}", result['win_amount'],
                result['server_seed'], result['client_seed'], result['nonce']
            )
            
            # Show result
            emoji = '✅' if result['win'] else '❌'
            
            await update.message.reply_text(
                f"""
{emoji} *Dice Result*

Roll: {result['result']}
Target: {result['target']} {direction}
{'🎉 YOU WIN!' if result['win'] else '😢 YOU LOSE'}

💰 Change: ${result['win_amount']:.2f}
💵 New Balance: ${db.get_user(user.id).balance:.2f}
🔑 Nonce: {result['nonce']}

🔐 *Provably Fair*
Server Seed: `{result['server_seed']}`
Client Seed: `{result['client_seed']}`

*Verify: SHA256({result['server_seed']}-{result['client_seed']}-{result['nonce']})*
""",
                parse_mode='Markdown'
            )
            
            # Show menu
            keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Click below to continue:", reply_markup=reply_markup)
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid input. Use: `50 over` or `30 under`",
                parse_mode='Markdown'
            )
            return GAME_CHOICE
    
    elif game == 'roulette':
        if text.startswith('number'):
            try:
                number = int(text.split()[1])
                if number < 0 or number > 36:
                    await update.message.reply_text(
                        "❌ Number must be 0-36",
                        parse_mode='Markdown'
                    )
                    return GAME_CHOICE
                
                # Play roulette
                result = games.roulette(bet, 'number', number, client_seed)
                
                # Update balance
                db.update_balance(user.id, result['win_amount'])
                db.save_game(
                    user.id, 'roulette', bet,
                    f"Number {result['result']}", result['win_amount'],
                    result['server_seed'], result['client_seed'], result['nonce']
                )
                
                emoji = '✅' if result['win'] else '❌'
                await update.message.reply_text(
                    f"""
{emoji} *Roulette Result*

Ball landed on: {result['result']}
Your bet: Number {number}
{'🎉 YOU WIN!' if result['win'] else '😢 YOU LOSE'}

💰 Change: ${result['win_amount']:.2f}
💵 New Balance: ${db.get_user(user.id).balance:.2f}
🔑 Nonce: {result['nonce']}

🔐 *Provably Fair*
Server Seed: `{result['server_seed']}`
Client Seed: `{result['client_seed']}`
""",
                    parse_mode='Markdown'
                )
                
                keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Click below to continue:", reply_markup=reply_markup)
                
            except ValueError:
                await update.message.reply_text(
                    "❌ Use: `number 7` for number bets",
                    parse_mode='Markdown'
                )
                return GAME_CHOICE
        else:
            # Color bets
            bet_type = text
            if bet_type not in ['red', 'black', 'even', 'odd']:
                await update.message.reply_text(
                    "❌ Use: red, black, even, odd, or number X",
                    parse_mode='Markdown'
                )
                return GAME_CHOICE
            
            result = games.roulette(bet, bet_type, 0, client_seed)
            
            # Update balance
            db.update_balance(user.id, result['win_amount'])
            db.save_game(
                user.id, 'roulette', bet,
                f"{bet_type} - {result['result']}", result['win_amount'],
                result['server_seed'], result['client_seed'], result['nonce']
            )
            
            emoji = '✅' if result['win'] else '❌'
            await update.message.reply_text(
                f"""
{emoji} *Roulette Result*

Ball landed on: {result['result']}
Your bet: {bet_type}
{'🎉 YOU WIN!' if result['win'] else '😢 YOU LOSE'}

💰 Change: ${result['win_amount']:.2f}
💵 New Balance: ${db.get_user(user.id).balance:.2f}
🔑 Nonce: {result['nonce']}

🔐 *Provably Fair*
Server Seed: `{result['server_seed']}`
Client Seed: `{result['client_seed']}`
""",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Click below to continue:", reply_markup=reply_markup)
    
    elif game == 'crash':
        try:
            target = float(text)
            if target < 1.01 or target > 100:
                await update.message.reply_text(
                    "❌ Target must be between 1.01 and 100.00",
                    parse_mode='Markdown'
                )
                return GAME_CHOICE
            
            result = games.crash(bet, target, client_seed)
            
            # Update balance
            db.update_balance(user.id, result['win_amount'])
            db.save_game(
                user.id, 'crash', bet,
                f"Crashed at {result['result']:.2f}x", result['win_amount'],
                result['server_seed'], result['client_seed'], result['nonce']
            )
            
            emoji = '✅' if result['win'] else '❌'
            await update.message.reply_text(
                f"""
{emoji} *Crash Result*

Crashed at: {result['result']:.2f}x
Target: {result['target']:.2f}x
{'🎉 YOU WIN!' if result['win'] else '💥 CRASHED!'}

💰 Change: ${result['win_amount']:.2f}
💵 New Balance: ${db.get_user(user.id).balance:.2f}
🔑 Nonce: {result['nonce']}

🔐 *Provably Fair*
Server Seed: `{result['server_seed']}`
Client Seed: `{result['client_seed']}`
""",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Click below to continue:", reply_markup=reply_markup)
            
        except ValueError:
            await update.message.reply_text(
                "❌ Enter a valid number (e.g., 1.50)",
                parse_mode='Markdown'
            )
            return GAME_CHOICE

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to menu"""
    query = update.callback_query
    await query.answer()
    await start_command(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Cancelled.\n\nType /start to play!",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# ==================== MAIN FUNCTION ====================

def main():
    try:
        token = os.getenv('BOT_TOKEN')
        if not token:
            logger.error("❌ BOT_TOKEN not set!")
            sys.exit(1)
        
        logger.info("🎰 BetAlgo is starting...")
        
        application = Application.builder().token(token).build()
        
        # Command handlers
        application.add
