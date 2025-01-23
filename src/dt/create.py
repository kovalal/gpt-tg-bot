from sqlalchemy.orm import Session

from models import User, Message, Completion
from clients.db import db_session_decorator


def create_message(message_dict, user):
    if message_dict.get('reply_to_message'):
        reply_to_message = message_dict['reply_to_message']['message_id']
    else:
        reply_to_message = None

    # Extract image details if available
    image_file_id = None
    image_metadata = None
    if 'photo' in message_dict and message_dict['photo']:
        # Get the highest resolution photo
        photo = message_dict['photo'][-1]
        image_file_id = photo['file_id']
        image_metadata = {
            "file_size": photo.get("file_size"),
            "width": photo.get("width"),
            "height": photo.get("height")
        }

    message = Message(
        id=message_dict['message_id'],
        date=message_dict['date'],
        chat_id=message_dict['chat']['id'],
        text=message_dict.get('text') or message_dict.get('caption'),
        user=user,
        reply_to_message=reply_to_message,
        image_file_id=image_file_id,
        image_metadata=image_metadata,
    )
    return message


# Example function to insert a message and user
@db_session_decorator
def save_message_to_db(message_dict: dict, session: Session = None):
    user_data = message_dict['from_user']
    user = session.query(User).get(user_data['id'])

    if not user:
        user = User(
            id=user_data['id'],
            username=user_data.get('username'),
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            is_bot=user_data['is_bot'],
            language_code=user_data.get('language_code'),
            is_premium=user_data.get('is_premium'),
        )
    session.add(user)

    message = create_message(message_dict, user)
    session.add(message)
    session.commit()


@db_session_decorator
def save_completion(completion_data: dict, message_ids: list, session: Session = None):
    """
    Save a Completion object into the database and link it to the specified messages.

    :param session: SQLAlchemy session instance
    :param completion_data: Dictionary containing completion fields from the API response
    :param message_ids: List of message IDs to link to the completion
    :return: The saved Completion object
    """
    # Extract data from the completion_data dictionary
    completion_id = completion_data.get("id")
    system_fingerprint = completion_data.get("system_fingerprint")
    created_timestamp = completion_data.get("created")
    model = completion_data.get("model")

    usage = completion_data.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    completion_tokens_details = usage.get("completion_tokens_details", {})

    # Create a Completion object
    completion = Completion(
        id=completion_id,
        system_fingerprint=system_fingerprint,
        #created=datetime.utcfromtimestamp(created_timestamp),
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        completion_tokens_details=completion_tokens_details
    )

    # Add the Completion to the session
    session.add(completion)

    # Link the Completion to the specified messages
    for message_id in message_ids:
        message = session.query(Message).filter_by(id=message_id).first()
        if message:
            message.completion = completion

    # Commit the changes to the database
    session.commit()

    return completion