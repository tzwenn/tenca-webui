document.addEventListener('DOMContentLoaded', () => {

	const $confirmation_field = document.getElementById('confirmation_phrase');
	const $delete_submit = document.getElementById('delete_submit');
	const $confirmation_reference = document.getElementById('confirmation_reference');

	if ($confirmation_field && $delete_submit && $confirmation_reference) {
		/* innerText should already be uppercase. This is just here in case some browsers
		 * or CSS-quirks come upon us in the future.
		 */
		const $confirmation_text = confirmation_reference.innerText.toUpperCase();
		$confirmation_field.addEventListener('input', () => {
			delete_submit.disabled = !($confirmation_field.value == $confirmation_text);
		});
		/* Run once to enable field in case of page-reload */
		delete_submit.disabled = !($confirmation_field.value == $confirmation_text);
	}
});