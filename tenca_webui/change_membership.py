from flask import Blueprint, abort, current_app, g, render_template, request
from markupsafe import escape

bp = Blueprint('change_membership', __name__)

def find_mailing_list(unescaped_hash_id):
	mailing_list = g.conn.get_list_by_hash_id(escape(unescaped_hash_id))
	if mailing_list is None:
		abort(404)
	return mailing_list

@bp.route('/<hash_id>/', methods=('GET', 'POST'))
def index(hash_id):
	mailing_list = find_mailing_list(hash_id)

	if request.method == 'POST':
		email = request.form["email"]
		# TODO: validate email
		joined, token = mailing_list.toggle_membership(email)
		current_app.logger.info('Received {} request for "{}", with token {}.'.format(
			'subscription' if joined else 'unsubscription',
			email, token
		))

		return render_template('change_membership/finished.html')

	return render_template('change_membership/index.html', mailing_list=mailing_list)
