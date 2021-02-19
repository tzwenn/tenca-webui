import logging

from markupsafe import escape
from flask import Flask

import tenca.connection
import tenca.settings
import tenca.exceptions


app = Flask(__name__)
logger = logging.Logger(__name__)

conn = tenca.connection.Connection()


################################################################################

def lookup_list_and_email_by_action(list_id, token):
	mailing_list = conn.get_list(list_id)
	try:
		email = mailing_list.pending_subscriptions()[token]
	except KeyError:
		# As of mailman<3.3.3 no unsubscriptions are exposed via
		# the REST API. This exception might be quite misleading.
		email = None
	return mailing_list, email


################################################################################


@app.route('/')
def index():
    return 'This is the main page! Here you can only log-in.'

@app.route('/confirm/<list_id>/<token>')
def confirm_action(list_id, token):
	mailing_list, email = lookup_list_and_email_by_action(escape(list_id), escape(token))
	
	try:
		mailing_list.confirm_subscription(escape(token))
	except tenca.exceptions.NoSuchRequestException:
		return 'Unknown action'     # TODO: better 404?

	if email is not None:
		conn.mark_address_verified(email)
		return 'Hi "%s", you successfully joined "%s"' % (email, mailing_list.fqdn_listname)
	else:
		return "ok. thx. bye."

@app.route('/report/<list_id>/<token>')
def report_action(list_id, token):
	mailing_list, email = lookup_list_and_email_by_action(escape(list_id), escape(token))
	
	logger.warn('Report received for list "{}" and token "{}" (address "{}")'.format(
		escape(list_id), escape(token), email
	))
	try:
		mailing_list.cancel_pending_subscription(escape(token))
	except tenca.exceptions.NoSuchRequestException:
		pass

	return 'Your report has been logged. Thank you.'

@app.route('/manage/<list_id>')
def manage_list(list_id):
    return 'This is the admin view for the owners of "%s" (requires login)!' % escape(list_id)

@app.route('/dashboard/<username>')
def user_dashboard(username):
    return 'This shows the lists "%s" is owner or member of (requires login)!' % escape(username)

@app.route('/<hashid>')
def subscribe_list(hashid):
	return 'Displaying (un)-subscription form of "%s"' % escape(hashid)