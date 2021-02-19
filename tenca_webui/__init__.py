import os

from flask import Flask
from flask_oidc import OpenIDConnect
from markupsafe import escape

import tenca.connection
import tenca.settings
import tenca.exceptions


def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='development',
	)

	if test_config is None:
		app.config.from_pyfile('config.py', silent=False)
	else:
		app.config.from_mapping(test_config)

	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

	################################################################################

	oidc = OpenIDConnect(app)
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
		return 'This is the main page!<br />Please <a href="/dashboard">log in</a>.'

	@app.route('/confirm/<list_id>/<token>/')
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

	@app.route('/report/<list_id>/<token>/')
	def report_action(list_id, token):
		mailing_list, email = lookup_list_and_email_by_action(escape(list_id), escape(token))
		
		app.logger.warn('Report received for list "{}" and token "{}" (address "{}")'.format(
			escape(list_id), escape(token), email
		))
		try:
			mailing_list.cancel_pending_subscription(escape(token))
		except tenca.exceptions.NoSuchRequestException:
			pass

		return 'Your report has been logged. Thank you.'

	@app.route('/manage/<list_id>/')
	@oidc.require_login
	def manage_list(list_id):
		return 'This is the admin view for the owners of "%s"!' % escape(list_id)

	@app.route('/dashboard/')
	@oidc.require_login
	def user_dashboard():
		return 'Here comes the lists "%s" is owner or member of.' % oidc.user_getfield('email')

	@app.route('/<hashid>/')
	def subscribe_list(hashid):
		return 'Displaying (un-)subscription form of "%s"' % escape(hashid)

	return app