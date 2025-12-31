// SPDX-FileCopyrightText: 2025-2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

if (window.matchMedia) {
	const stylesheet = document.querySelector('link[rel="stylesheet"][href="/univention/theme.css"]');
	if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
		stylesheet.setAttribute('href', '/univention/themes/dark.css');
	} else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
		stylesheet.setAttribute('href', '/univention/themes/light.css');
	}
}
