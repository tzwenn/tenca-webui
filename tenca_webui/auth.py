from flask_oidc import OpenIDConnect

oidc = OpenIDConnect()

def is_current_user(email):
	return email == oidc.user_getfield('email')