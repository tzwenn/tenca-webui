document.addEventListener('DOMContentLoaded', () => {

	/*************************************************************************
	 * Manually disable deletion button if confirmation phrase is wrong
	 */

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

	/*************************************************************************
 	* Boolean list options are represented with Checkboxes and send to server using AJAX
 	*/

	$rootE = document.documentElement;

	function openModal()
	{
		const $modal = document.getElementById('switch-error-modal');
		document.documentElement.classList.add('is-clipped');
		$modal.classList.add('is-active');
	}

	function closeModal()
	{
		const $modal = document.getElementById('switch-error-modal');
		$rootE.classList.remove('is-clipped');
		$modal.classList.remove('is-active');
	}

	const $modalCloser = Array.prototype.slice.call(document.querySelectorAll('.modal-background, .modal-close, .modal-inner-close'), 0);
	if ($modalCloser.length > 0) {
		$modalCloser.forEach( el => {
			el.addEventListener('click', closeModal);
		});
	}

	document.addEventListener('keydown', event => {
        var e = event || window.event;
        if (e.keyCode === 27) {
            closeModal();
        }
    });

	const $switches = Array.prototype.slice.call(document.querySelectorAll('.tenca-list-option'), 0);
	if ($switches.length > 0) {
		$switches.forEach( $switch => {
			$switch.addEventListener('click', () => {
				var req = new XMLHttpRequest();
				req.addEventListener('load', () => {
					if (req.status != 200) {
						$switch.checked = !$switch.checked;
						openModal();
					}
				});

				req.open("POST", $switch.dataset.tencaTarget);
				req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
				req.setRequestHeader("X-CSRFToken", csrf_token);
				req.send(JSON.stringify({name: $switch.name, value: $switch.checked}));
			});
		});
	}
});
