"""資料庫模型與初始化"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum
import os

Base = declarative_base()


class Position(enum.Enum):
    """測量側"""
    LEFT = "左手"
    RIGHT = "右手"


class BloodPressureRecord(Base):
    """血壓記錄模型"""
    __tablename__ = 'blood_pressure_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), default='default')
    systolic = Column(Integer, nullable=False)  # 收縮壓
    diastolic = Column(Integer, nullable=False)  # 舒張壓
    pulse = Column(Integer, nullable=False)  # 脈搏
    measured_at = Column(DateTime, default=datetime.now)  # 測量時間
    position = Column(Enum(Position), default=Position.LEFT)  # 測量側
    note = Column(Text)  # 備註
    category = Column(String(20))  # WHO 分級標籤


class UserSettings(Base):
    """用戶設定模型"""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), default='default', unique=True)
    age = Column(Integer)
    gender = Column(String(10))
    weight = Column(Integer)  # 體重（公斤）


# 資料庫路徑
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hearttrack.db')

# 建立資料庫引擎
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)

# 建立 Session
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """初始化資料庫，建立所有表格"""
    Base.metadata.create_all(engine)


def get_session():
    """取得資料庫 session"""
    return SessionLocal()


