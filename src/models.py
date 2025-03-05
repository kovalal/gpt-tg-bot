from sqlalchemy import (Column, Integer, String, Boolean, DateTime, ForeignKey, Text,
                         BigInteger, JSON, Float, PrimaryKeyConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime

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
    settings = Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)

    # Relationships
    messages = relationship("Message", back_populates="user")
    payments = relationship("Payment", back_populates="user")

    def gpt_role(self):
        if self.is_bot:
            return 'assistant'
        return 'user'

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def set_settings(self, settings_name, settings_value):
        """
        Обновляет или добавляет значение настройки с ключом settings_name.
        При этом все другие настройки остаются нетронутыми.
        """
        if self.settings is None:
            self.settings = {}
        self.settings[settings_name] = settings_value

    def get_settings(self, settings_name):
        if self.settings is None:
            settings = {}
        else:
            settings = self.settings
        default_value = config.default_user_settings[settings_name]
        return settings.get(settings_name, default_value)


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

    audio_file_id = Column(String, nullable=True)  # Telegram file ID для аудио
    audio_metadata = Column(JSON, nullable=True)   # Метаданные аудио (например, длительность, mime_type, размер файла)

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
        
        #if self.audio_file_id and bot:
        #    base64_audio = await retrieve_audio_base64(bot, self.audio_file_id)
        #    content.append({
        #        "type": "input_audio",
        #        "input_audio": {
        #            "data": base64_audio,
        #            "format": "wav"  
        #        }
        #    })

        # Use OpenAI's replica representation method
        return {"content": content, "role": self.get_role()}
    

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


class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    telegram_payment_charge_id = Column(String, nullable=False)
    provider_payment_charge_id = Column(String, nullable=True)
    total_amount = Column(Integer, nullable=False)  # сумма в копейках
    currency = Column(String, nullable=False)
    invoice_payload = Column(String, nullable=False)
    status = Column(String, nullable=True)  # например, "succeeded", "failed" и т.д.
    created = Column(DateTime, default=datetime.utcnow)
    
    # Связь с пользователем
    user = relationship("User", back_populates="payments")