from flask import Blueprint, Markup, abort, current_app, escape, flash, g, render_template

import tenca.exceptions

from ._macros import css_codify

bp = Blueprint('action', __name__)

def lookup_list_and_email_by_action(list_id, token):
	mailing_list = g.conn.get_list(list_id)
	if mailing_list is None:
		abort(404)
	try:
		email = mailing_list.pending_subscriptions()[token]
	except KeyError:
		# As of mailman<3.3.3 no unsubscriptions are exposed via
		# the REST API. This exception might be quite misleading.
		email = None
	return mailing_list, email

@bp.route('/confirm/<list_id>/<token>/')
def confirm_action(list_id, token):
	mailing_list, email = lookup_list_and_email_by_action(escape(list_id), escape(token))

	try:
		mailing_list.confirm_subscription(escape(token))
	except tenca.exceptions.NoSuchRequestException:
		abort(404)

	if email is not None:
		g.conn.mark_address_verified(email)
		flash(Markup('{} has successfully joined {}.'.format(email, css_codify(mailing_list.fqdn_listname))), category='success')
	else:
		flash(Markup('Ok. Thx. Bye from {}.'.format(css_codify(mailing_list.fqdn_listname))), category='success')
	
	return render_template('action.html')

@bp.route('/report/<list_id>/<token>/')
def report_action(list_id, token):
	mailing_list, email = lookup_list_and_email_by_action(escape(list_id), escape(token))

	current_app.logger.warn('Report received for list "{}" and token "{}" (address "{}")'.format(
		escape(list_id), escape(token), email
	))
	try:
		mailing_list.cancel_pending_subscription(escape(token))
	except tenca.exceptions.NoSuchRequestException:
		pass # We don't tell.

	flash('Your report has been logged. Thank you.', category='success')

	return render_template('action.html')

