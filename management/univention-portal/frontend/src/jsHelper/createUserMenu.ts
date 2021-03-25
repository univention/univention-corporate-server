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
import { changePassword } from '@/jsHelper/umc';
import { translate } from '@/i18n/translations';

function changePasswordCallback(tileClick) {
  tileClick.$store.dispatch('navigation/setActiveButton', '');
  tileClick.$store.dispatch('modal/setShowModalPromise', {
    name: 'ChangePassword',
    stubborn: true,
  }).then((values) => {
    changePassword(values.oldPassword, values.newPassword).then(() => {
      tileClick.$store.dispatch('notificationBubble/addSuccessNotification', {
        bubbleTitle: translate('CHANGE_PASSWORD'),
        bubbleDescription: translate('CHANGE_PASSWORD_SUCCESS'),
      });
      tileClick.$store.dispatch('modal/setHideModal');
    }, (error) => {
      tileClick.$store.dispatch('notificationBubble/addErrorNotification', {
        bubbleTitle: translate('CHANGE_PASSWORD'),
        bubbleDescription: `${error}`,
      });
      tileClick.$store.dispatch('modal/setHideModal');
      return changePasswordCallback(tileClick);
    });
  }, () => {
    tileClick.$store.dispatch('modal/setHideModal');
  });
}

export default function createUserMenu(portalData) {
  const menuTitle = {
    de_DE: 'Benutzereinstellungen',
    en_US: 'User settings',
    fr_FR: 'Réglages utilisateur',
  };

  const subMenuItems = [{
    title: {
      en_US: 'Change password',
      de_DE: 'Passwort ändern',
    },
    linkTarget: 'internalFunction',
    internalFunction: changePasswordCallback,
    links: [],
  }];

  const menuElement = {
    title: menuTitle,
    linkTarget: 'samewindow',
    subMenu: subMenuItems,
  };
  return menuElement;
}
