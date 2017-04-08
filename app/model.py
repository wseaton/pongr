from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Text, create_engine, MetaData, Float, Boolean

db = SQLAlchemy()


class Game(db.Model):
    id = Column(Integer, primary_key=True)
    player_a = Column(Text, unique=False)
    player_b = Column(Text, unique=False)
    score_a = Column(Integer, unique=False)
    score_b = Column(Integer, unique=False)
    timestamp = Column(Integer, unique=False)
    deleted = Column(Boolean, unique=False)


class DoublesGame(db.Model):
    id = Column(Integer, primary_key=True)
    player_a_team_a = Column(Text, unique=False)
    player_b_team_a = Column(Text, unique=False)
    player_a_team_b = Column(Text, unique=False)
    player_b_team_b = Column(Text, unique=False)
    score_team_a = Column(Integer, unique=False)
    score_team_b = Column(Integer, unique=False)
    timestamp = Column(Integer, unique=False)
    deleted = Column(Boolean, unique=False)


class Player(db.Model):
    player_id = Column(Integer, primary_key=True)
    first_name = Column(Text, unique=False)
    last_name = Column(Text, unique=False)
    alias = Column(Text, unique=True)


class Ratings(db.Model):
    alias = Column(Text, primary_key=True)
    rating = Column(Float, unique=False)
    sigma = Column(Float, unique=False)
    tau = Column(Float, unique=False)
    pi = Column(Float, unique=False)
    trueskill = Column(Float, unique=False)