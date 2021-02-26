from flask import Markup, flash, g, render_template, request, url_for

def css_codify(s):
	return '<span class="is-family-code wrappable-list-id">{}</span>'.format(s)

def index():
	if request.method == 'POST':
		try:
			new_list = g.conn.add_list(request.form['listname'], g.oidc.user_getfield('email'))
		except Exception as e:
			flash(Markup('An error occurred: {}'.format(e)), category='danger')
		else:
			flash(Markup((
				'Successfully created {}.<br />'
				'Manage your new list <a href="{}">here</a>.'
			).format(css_codify(new_list.fqdn_listname), url_for('manage_list', list_id=new_list.list_id))),
				category='success')


	email = g.oidc.user_getfield('email')
	memberships = g.conn.get_owner_and_memberships(email)

	return render_template('dashboard.html', memberships=memberships)
