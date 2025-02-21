import uuid

from pydantic import EmailStr, model_validator,field_validator
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime
from sqlmodel import SQLModel, Field, String, ARRAY ,JSON
from sqlalchemy.dialects.postgresql import JSONB

from typing import List, Optional, Set
from sqlalchemy.sql.schema import Column
from sqlalchemy import event, Computed


from sqlalchemy.dialects import postgresql #ARRAY contains requires dialect specific type



class BaseSQLModel(SQLModel):
    class Config:
        from_attributes = True
    id: int= Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    

class ItemBase(BaseSQLModel):
    __table_args__ = {'extend_existing': True}
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class UserBase(BaseSQLModel):
    __table_args__ = {'extend_existing': True}
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

class Channels(BaseSQLModel,table=True):
    name: str
    description: str
    profiles: list["Profiles"] = Relationship(back_populates="channel")

class Profiles(BaseSQLModel,table=True):
    name: str
    description: str = Field(default=None,nullable=True)
    keywords: Optional[Set[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    channel_id: int = Field(default=None,foreign_key='channels.id')
    channel: Channels = Relationship(back_populates="profiles")
    posts: list["Posts"] = Relationship(back_populates="author")
    link : str
    @property
    def channel_name(self) -> str:
        return f"{self.channel.name}"

class Followers(BaseSQLModel,table=True):
    profile_id: int = Field(default=None,foreign_key='profiles.id')
    follower_id: int = Field(default=None,foreign_key='profiles.id')

class Posts(BaseSQLModel,table=True):
    title: str = Field(max_length=255,nullable=True)
    content: str
    description: str = Field(default=None,nullable=True)
    link: str
    author_id: int = Field(default=None,foreign_key='profiles.id')
    author: Profiles = Relationship(back_populates="posts")
    status: str = Field(default='not_processed')
    posted_at: datetime
    processed_results: "ProcessedResults" = Relationship(back_populates="post")
    @property
    def author_name(self) -> str:
        return f"{self.author.name}"

class ProcessedResults(BaseSQLModel,table=True):
    __tablename__ = 'processed_results'
    is_mentioned: bool = Field(default=False)
    sentiment: str = Field(default=None,nullable=True)
    project_name: str = Field(default=None,nullable=True)
    summarization: str = Field(default=None,nullable=True)
    keywords: Optional[Set[str]] = Field(default=None, sa_column=Column(postgresql.ARRAY(String())))
    post_id: int = Field(default=None,foreign_key='posts.id')
    post: Posts = Relationship(back_populates="processed_results")
    processed_at: datetime

class Tokens(BaseSQLModel,table=True):
    cgc_id: str
    cmc_id: str = Field(default=None,nullable=True)
    symbol: str
    name: str 
    market_cap_rank: int
    search_text: str = Field(default=None,nullable=True)
    token_market_data: List["TokenMarketData"] = Relationship(back_populates="token")

# class Sentences(BaseSQLModel,table=True):
#     sentence: str
#     posts: Posts = Relationship(back_populates="sentences")
#     post_id: int = Field(default=None,foreign_key='posts.id')
#     vector_id: str
class ROI(SQLModel):
    times: float
    currency: str
    percentage: float

class TokenMarketData(BaseSQLModel,table=True):
    __tablename__ = 'token_market_data'
    token_id: int = Field(default=None,foreign_key='tokens.id')
    token: Tokens = Relationship(back_populates="token_market_data")
    symbol: str = Field(default=None,nullable=True)
    name: str = Field(default=None,nullable=True)
    image: str = Field(default=None,nullable=True)
    current_price: float
    market_cap: float = Field(default=None,nullable=True)
    market_cap_rank: int = Field(default=None,nullable=True)
    fully_diluted_valuation: float = Field(default=None,nullable=True)
    total_volume: float = Field(default=None,nullable=True)
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_change_24h: float
    market_cap_change_percentage_24h: float
    circulating_supply: float
    total_supply: float = Field(default=None,nullable=True)
    max_supply: Optional[float] = None
    ath: float
    ath_change_percentage: float
    ath_date: datetime
    atl: float
    atl_change_percentage: float
    atl_date: datetime
    roi: dict = Field(sa_type=JSONB, nullable=True)
    last_updated: datetime

class PostPersonas(BaseSQLModel,table=True):
    __tablename__ = "post_personas"
    username: str = Field(default=None,nullable=True)
    age: int = Field(default=None,nullable=True)
    country: str = Field(default=None,nullable=True)
    profession: str = Field(default=None,nullable=True)
    financial_status: str = Field(default=None,nullable=True)
    personality: str = Field(default=None,nullable=True)
    likes: str =Field(default=None,nullable=True)
    dislikes: str = Field(default=None,nullable=True)
    posting_style: str = Field(default=None,nullable=True)
    daily_post_frequency: str = Field(default=None,nullable=True)
    twitter_app_id: str = Field(default=None,nullable=True)

class TwitterCredentials(BaseSQLModel,table=True):
    __tablename__ = "twitter_credentials"
    app_id: str =Field(default=None,nullable=True)
    consumer_key: str =Field(default=None,nullable=True)
    consumer_secret: str =Field(default=None,nullable=True)
    bearer_token: str =Field(default=None,nullable=True)
    access_token: str =Field(default=None,nullable=True)
    access_secret: str =Field(default=None,nullable=True)

class User(UserBase, table=True):
    #id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    #items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


class Item(ItemBase, table=False):
    #id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    # owner_id: int = Field(
    #     foreign_key="user.id", nullable=True, ondelete="CASCADE"
    # )
    #owner: User | None = Relationship(back_populates="items")
# Shared properties

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(BaseSQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(BaseSQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(BaseSQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)

# Database model, database table inferred from class name



# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(BaseSQLModel):
    data: list[UserPublic]
    count: int





# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(BaseSQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(BaseSQLModel):
    message: str


# JSON payload containing access token
class Token(BaseSQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseSQLModel):
    sub: str | None = None


class NewPassword(BaseSQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

@event.listens_for(BaseSQLModel, 'before_update', propagate=True)
def update_timestamp(mapper, connection, target):
    target.updated_at = datetime.now()

@event.listens_for(Tokens, 'before_update', propagate=True)
def update_search_field(mapper, connection, target):
    target.search_text = f"{target.symbol} {target.name}"