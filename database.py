from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    balance = Column(Float, default=Config.STARTING_BALANCE)
    total_bet = Column(Float, default=0)
    total_win = Column(Float, default=0)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class GameHistory(Base):
    __tablename__ = 'game_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    game_type = Column(String(50))
    bet_amount = Column(Float)
    result = Column(String(50))
    win_amount = Column(Float)
    server_seed = Column(String(100))
    client_seed = Column(String(100))
    nonce = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

class Database:
    @staticmethod
    def get_session():
        return SessionLocal()
    
    @staticmethod
    def get_user(telegram_id):
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id)
                session.add(user)
                session.commit()
            return user
        finally:
            session.close()
    
    @staticmethod
    def update_balance(telegram_id, amount):
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.balance += amount
                user.last_active = datetime.utcnow()
                session.commit()
                return user.balance
            return None
        finally:
            session.close()
    
    @staticmethod
    def save_game(telegram_id, game_type, bet_amount, result, win_amount, server_seed, client_seed, nonce):
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.games_played += 1
                if win_amount > 0:
                    user.games_won += 1
                user.total_bet += bet_amount
                user.total_win += win_amount
            
            game = GameHistory(
                user_id=telegram_id,
                game_type=game_type,
                bet_amount=bet_amount,
                result=result,
                win_amount=win_amount,
                server_seed=server_seed,
                client_seed=client_seed,
                nonce=nonce
            )
            session.add(game)
            session.commit()
        finally:
            session.close()
