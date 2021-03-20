/*
 * Copyright 2021 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
const setCookie = (name, value) => {
  const date = new Date();

  let cookieValue = escape(new Date(date.setFullYear(date.getFullYear())).toUTCString());
  let expiryDate = new Date(date.setFullYear(date.getFullYear() + 1)).toUTCString();

  if (name === '') {
    console.error('setCookie: Missing name! Aborted!');
    return false;
  }

  if (value === '') {
    cookieValue = '';
    expiryDate = -1;
  }

  // set cookie
  document.cookie = `${name}=${cookieValue};expires=${expiryDate}; path=/`;

  return false;
};

const getCookie = (name) => {
  const nameEQ = `${name}=`;
  const ca = document.cookie.split(';');
  let ret = '';

  for (let i = 0; i < ca.length; i += 1) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) {
      ret = c.substring(nameEQ.length, c.length);
    }
  }

  return ret;
};

const deleteCookie = (name) => {
  setCookie(name, '', -1);
};

export {
  setCookie,
  getCookie,
  deleteCookie,
};
