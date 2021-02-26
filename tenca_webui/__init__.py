import urllib.error
import os

from flask import Flask, abort, g, redirect, render_template, url_for
from flask_oidc import OpenIDConnect
from markupsafe import escape

import tenca.connection
import tenca.settings
import tenca.exceptions


def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='development',
		BRAND_CAPTION='Tenca',
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

	from tenca_webui import db
	db.init_db(app)

	oidc = OpenIDConnect(app)
	conn = tenca.connection.Connection() #db.SQLHashStorage)

	@app.before_request
	def before_request():
		g.oidc = oidc
		g.conn = conn

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
		if oidc.user_loggedin:
			return redirect(url_for('dashboard'))
		else:
			return render_template('index.html')

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
		mailing_list = conn.get_list(escape(list_id))
		if mailing_list is None or not mailing_list.is_owner(oidc.user_getfield('email')):
			abort(404)

		return render_template('manage_list.html', mailing_list=mailing_list)

	@app.route('/dashboard/')
	@oidc.require_login
	def dashboard():
		email = oidc.user_getfield('email')
		member_of = conn.find_lists(email, role='member')
		owner_of = conn.find_lists(email, role='owner')
		return render_template('dashboard.html', member_of=member_of, owner_of=owner_of)

	@app.route('/logout/')
	def logout():
		oidc.logout()
		return redirect(url_for('index'))

	@app.route('/<hash_id>/')
	def change_membership(hash_id):
		mailing_list = conn.get_list_by_hash_id(escape(hash_id))
		if mailing_list is None:
			abort(404)
		return render_template('change_membership.html', mailing_list=mailing_list)

	@app.route('/<hash_id>/<legacy_admin_token>/')
	@oidc.require_login
	def legacy_manage_list(hash_id, legacy_admin_token):
		mailing_list = conn.get_list_by_hash_id(escape(hash_id))
		if mailing_list is None:
			abort(404)

		# If owner: Forward
		# If member: Promote & Forward
		# If not member: Request to join first
		return 'Forwarding to the management form of "%s", if "%s" is the correct token.' % ( mailing_list.fqdn_listname, escape(legacy_admin_token))

	return app