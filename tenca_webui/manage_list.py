from flask import Blueprint, Markup, abort, escape, flash, g, render_template, request, url_for

from .auth import oidc

bp = Blueprint('manage_list', __name__, url_prefix='/manage')

@bp.route('/<list_id>/')
@oidc.require_login
def index(list_id):
	mailing_list = g.conn.get_list(escape(list_id))
	if mailing_list is None or not mailing_list.is_owner(oidc.user_getfield('email')):
		abort(404)

	list_bool_options = [
		('notsubscribed_allowed_to_post', 'Not subscribed users are allowed to post.', mailing_list.notsubscribed_allowed_to_post),
		('replies_addressed_to_list', 'Replies are addressed to the list per default.', True),
	]

	return render_template('manage_list.html', mailing_list=mailing_list, list_bool_options=list_bool_options)
