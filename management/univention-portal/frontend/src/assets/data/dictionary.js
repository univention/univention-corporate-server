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
import { ref } from 'vue';

function _(msg) {
  return {
    original: msg,
    translated: ref(msg),
  };
}

const catalog = {
  NOTIFICATIONS: _('Notifications'),
  LOGIN: _('Login'),
  LOGOUT: _('Logout'),
  EDIT_PORTAL: _('Edit portal'),
  STOP_EDIT_PORTAL: _('Stop edit portal'),
  SWITCH_LOCALE: _('Switch locale'),
  COOKIE_SETTINGS: _('Cookie Settings'),
  COOKIE_DESCRIPTION: _('We use cookies in order to provide you with certain functions and to be able to guarantee an unrestricted service. By clicking on "Accept", you consent to the collection of information on this portal.'),
  ACCEPT: _('Accept'),
  SUBMIT: _('Submit'),
  DISMISS_NOTIFICATION: _('Dismiss notification'),
  LOGIN_REMINDER_DESCRIPTION: _('Login <a class="notification-bubble__link" href="#">here</a> so that you can use the full range of functions of UCS.'),
  ADD_CATEGORY: _('Add category'),
  EDIT_CATEGORY: _('Edit category'),
  ADD_ENTRY: _('Add entry'),
  CREATE_ENTRY: _('Create new entry'),
  ADD_NEW_ENTRY: _('Add existing entry'),
  ADD_FOLDER: _('Add folder'),
  CREATE_FOLDER: _('Create new folder'),
  ADD_NEW_FOLDER: _('Add existing folder'),
  CANCEL: _('Cancel'),
  SAVE: _('Save'),
  REMOVE_FROM_PORTAL: _('Remove from this portal'),
  INTERNAL_NAME: _('Internal name'),
  DISPLAY_NAME: _('Display name'),
  LANGUAGE_CODE: _('Language code (e.g. en_US)'),
  MODAL_HINT_CATEGORIES: _('Display name of the category. At least one entry; strongly encouraged to have one for en_US'),
  COOKIE_TITLE: _('Cookie Settings'),
  COOKIE_TEXT: _('We use cookies in order to provide you with certain functions and to be able to guarantee an unrestricted service. By clicking on "Accept", you consent to the collection of information on this portal.'),
  OLD_PASSWORD: _('Old password'),
  NEW_PASSWORD: _('New password'),
  RETYPE: _('retype'),
  CHANGE_PASSWORD: _('Change password'),
  CHANGE_PASSWORD_SUCCESS: _('You have successfully updated your password'),
  REMOVE: _('Remove'),
  UPLOAD: _('Upload'),
  SELECT_FILE: _('Select file'),
  GO_TO: _('Go to'),
  START: _('Start'),
  STOP: _('Stop'),
  OPEN: _('Open'),
  EDIT_MODE: _('Edit mode'),
  SIDEBAR: _('sidebar'),
  SEARCH: _('search'),
  NOTIFCATIONS: _('Notifications'),
  MENU: _('Menu'),
  TABS: _('Tabs'),
  CHOOSE_TAB: _('Choose a tab'),
  SHOW_UMC: _('Show local UMC modules'),
};

export { catalog };
