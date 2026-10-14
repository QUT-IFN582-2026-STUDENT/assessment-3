from .models import UserInfo

from flask import session

def get_user():
    user_dict = session.get('user')
    if user_dict:
        return UserInfo(
            id=str(user_dict['user_id']),
            username=user_dict.get('username', ''),
            firstname=user_dict['first_name'],
            lastname=user_dict['last_name'],
            email=user_dict['email'],
            phone=user_dict['phone']
        )
    return None