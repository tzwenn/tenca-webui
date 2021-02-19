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
		return 'This is the main page!<br />Please <a href="/dashboard">log in</a> to create lists.'

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
		email = oidc.user_getfield('email')
		member_of = conn.find_lists(email, role='member')
		owner_of = conn.find_lists(email, role='owner')

		def format_enumeration(lists):
			return "\n".join('<li><a href="/%s">%s</a></li>' % (list.hashid, list.fqdn_listname) for list in lists)

		return "\n".join('<p>{}</p>'.format(par) for par in (
			'Hi {},',
			'you are owner of:',
			'<ul>{}</ul>',
			'and member of:',
			'<ul>{}</ul>',
		)).format(
			email,
			format_enumeration(owner_of),
			format_enumeration(member_of),
		)

	@app.route('/<hashid>/')
	def subscribe_list(hashid):
		return 'Displaying (un-)subscription form of "%s"' % escape(hashid)

	@app.route('/<hashid>/<legacy_admin_token>/')
	@oidc.require_login
	def legacy_manage_list(hashid, legacy_admin_token):
		return 'Forwarding to the management form of "%s", if "%s" is the correct token.' % (escape(hashid), escape(legacy_admin_token))

	return app