from flask import Blueprint, Markup, abort, current_app, flash, g, render_template, request
from markupsafe import escape
from wtforms import Form, validators
from wtforms.fields.html5 import EmailField

bp = Blueprint('change_membership', __name__)

def find_mailing_list(unescaped_hash_id):
	mailing_list = g.conn.get_list_by_hash_id(escape(unescaped_hash_id))
	if mailing_list is None:
		abort(404)
	return mailing_list

class SubscriptionForm(Form):
	email = EmailField('E-Mail Address', [validators.Email()])

@bp.route('/<hash_id>/', methods=('GET', 'POST'))
def index(hash_id):
	mailing_list = find_mailing_list(hash_id)
	form = SubscriptionForm(request.form)

	if request.method == 'POST' and form.validate():
		try:
			joined, token = mailing_list.toggle_membership(form.email.data)
		except Exception as e:
			flash(Markup("An Error occurred: {}".format(escape(str(e)))), category="danger");
		else:
			current_app.logger.info('Received {} request for "{}", with token {}.'.format(
				'subscription' if joined else 'unsubscription',
				form.email.data, token
			))

			return render_template('change_membership/finished.html')

	return render_template('change_membership/index.html', form=form, mailing_list=mailing_list)
