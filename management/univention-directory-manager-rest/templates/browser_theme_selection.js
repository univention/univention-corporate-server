if (window.matchMedia) {
	const stylesheet = document.querySelector('link[rel="stylesheet"][href="/univention/theme.css"]');
	if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
		stylesheet.setAttribute('href', '/univention/themes/dark.css');
	} else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
		stylesheet.setAttribute('href', '/univention/themes/light.css');
	}
}
