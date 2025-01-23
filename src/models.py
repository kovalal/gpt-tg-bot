from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, Text,
                         BigInteger, JSON, Float, PrimaryKeyConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from clients.gpt import replica_repr
from tools import retrieve_image_base64
import config

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, index=True)  # Telegram user ID
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_bot = Column(Boolean, nullable=False)
    language_code = Column(String, nullable=True)
    is_premium = Column(Boolean, nullable=True)
    model = Column(String, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="user")

    def gpt_role(self):
        if self.is_bot:
            return 'assistant'
        return 'user'

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Message(Base):
    __tablename__ = 'messages'

    id = Column(BigInteger, nullable=False)  # Telegram message ID
    date = Column(DateTime, nullable=False)
    chat_id = Column(Integer, nullable=False)  # Chat ID
    text = Column(Text, nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    reply_to_message = Column(BigInteger, nullable=True)
    completion_id = Column(String, ForeignKey("completions.id"), nullable=True)
    image_file_id = Column(String, nullable=True)  # Telegram file ID
    image_metadata = Column(JSON, nullable=True)  # Additional image metadata (e.g., size, type)

    # Relationships
    user = relationship("User", back_populates="messages")
    completion = relationship("Completion", back_populates="messages")
    
    __table_args__ = (
        PrimaryKeyConstraint('chat_id', 'id'),
    )

    def get_role(self):
        return 'assistant' if self.user.is_bot else 'user'

    async def gpt_repr(self, bot=None):
        content = []
        if self.completion:
            text = ''.join([m.text for m in self.completion.messages if self.user == m.user])
            content.append({"type": "text", "text": text})
        else:
            content.append({"type": "text", "text": self.text})

        # Include the image content if it exists
        if self.image_file_id and bot:
            base64_image = await retrieve_image_base64(bot, self.image_file_id)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

        # Use OpenAI's replica representation method
        return replica_repr(content, self.get_role())
    

class Completion(Base):
    __tablename__ = 'completions'

    id = Column(String, primary_key=True)  # e.g., "chatcmpl-123"
    system_fingerprint = Column(String, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)
    model = Column(String, nullable=False)

    # Usage fields
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    completion_tokens_details = Column(JSON, nullable=True)

    cost = Column(Float, nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="completion")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.calculate_cost()

    def calculate_cost(self):
        # Example cost calculation
        # Replace with your actual pricing logic
        model_name = self.model or config.model_config['default']
        model_pricing = config.model_config.get(model_name)
        if not model_pricing:
            raise ValueError(f"Pricing configuration not found for model: {self.model}")

        pricing = model_pricing['pricing']
        input_token_cost = pricing['input_tokens']
        cached_input_token_cost = pricing['cached_input_tokens']
        output_token_cost = pricing['output_tokens']

        # Extract details from completion_tokens_details
        cached_input_tokens = self.completion_tokens_details.get("cached_input_tokens", 0) if self.completion_tokens_details else 0

        # Calculate costs
        input_cost = (self.prompt_tokens * input_token_cost) / 10 ** 6
        cached_cost = (cached_input_tokens * cached_input_token_cost) / 10 ** 6
        output_cost = (self.completion_tokens * output_token_cost) / 10 ** 6

        # Assign the total cost
        self.cost = input_cost + cached_cost + output_cost