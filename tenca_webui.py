from markupsafe import escape
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'This is the main page! Here you can only log-in'

@app.route('/confirm/<list_id>/<token>')
def confirm_action(list_id, token):
	return 'So, you want to confirm your action "%s" on list "%s"?' % (escape(list_id), escape(token))

@app.route('/report/<list_id>/<token>')
def report_action(list_id, token):
	return 'I will log your complain with "%s" on list "%s"?' % (escape(list_id), escape(token))

@app.route('/manage/<list_id>')
def manage_list(list_id):
    return 'This is the admin view for the owners of "%s" (requires login)!' % escape(list_id)

@app.route('/dashboard/<username>')
def user_dashboard(username):
    return 'This shows the lists "%s" is owner or member of (requires login)!' % escape(username)

@app.route('/<hashid>')
def subscribe_list(hashid):
	return 'Displaying (un)-subscription form of "%s"' % escape(hashid)