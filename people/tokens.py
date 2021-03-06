import jwt
import time

def get_invite_token(email, expires_in=259200):
    return jwt.encode(
        {'invited_email': email, 'exp': time.time() + expires_in},
        settings.SECRET_KEY, algorithm='HS256').decode('utf-8')


def verify_invite_token(token):
    try:
        email, exp_time = jwt.decode(token, app.config['SECRET_KEY'],
                                     algorithms=['HS256'])
        invite = ParentInvite.objects.get(email=email)
    except:
        return
    return (exp_time < time.time()) and invite
