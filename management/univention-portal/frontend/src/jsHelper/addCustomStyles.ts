/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// This function is necessary to make sure that the custom.css overrides all the other styles without the use of import.
export default function addCustomStyles(): void {
  const themeCss = document.createElement('link');
  themeCss.rel = 'stylesheet';
  themeCss.href = process.env.VUE_APP_THEME_PATH || '/univention/theme.css';
  document.head.appendChild(themeCss);

  const customCss = document.createElement('link');
  customCss.rel = 'stylesheet';
  customCss.href = './css/custom.css';
  document.head.appendChild(customCss);
}
