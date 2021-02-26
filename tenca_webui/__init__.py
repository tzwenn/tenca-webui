import urllib.error
import os

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for
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

	@app.errorhandler(404)
	def page_not_found(e):
		return render_template('404.html'), 404

	################################################################################

	@app.route('/')
	def index():
		if oidc.user_loggedin:
			return redirect(url_for('dashboard'))
		else:
			return render_template('index.html')

	from . import action
	app.register_blueprint(action.bp)

	# Atm, I don't know how to plug oidc into a Blueprint.
	# Hence, this ugly hack here. Sorry.
	@app.route('/dashboard/', methods=('GET', 'POST'))
	@oidc.require_login
	def dashboard():
		from . import dashboard
		return dashboard.index()

	@app.route('/manage/<list_id>/')
	@oidc.require_login
	def manage_list(list_id):
		from . import manage_list
		return manage_list.index(list_id)

	@app.route('/logout/')
	def logout():
		oidc.logout()
		return redirect(url_for('index'))

	from . import change_membership
	app.register_blueprint(change_membership.bp)

	@app.route('/<hash_id>/<legacy_admin_token>/')
	@oidc.require_login
	def legacy_manage_list(hash_id, legacy_admin_token):
		mailing_list = change_membership.find_mailing_list(hash_id)

		# If owner: Forward
		# If member: Promote & Forward
		# If not member: Request to join first
		return 'Forwarding to the management form of "%s", if "%s" is the correct token.' % (mailing_list.fqdn_listname, escape(legacy_admin_token))

	return app