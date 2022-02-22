/*
 * Copyright 2021-2022 Univention GmbH
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
import _ from '@/jsHelper/translate';
import { changePassword } from '@/jsHelper/umc';
import { randomId } from '@/jsHelper/tools';

function makeEntry(entryID, availableTiles, defaultLinkTarget) {
  const entry = availableTiles.find((tile) => tile.dn === entryID);
  if (!entry) {
    return null;
  }
  return {
    id: `menu-item-${randomId()}`,
    title: entry.name,
    description: entry.description,
    links: entry.links,
    linkTarget: entry.linkTarget === 'useportaldefault' ? defaultLinkTarget : entry.linkTarget,
    pathToLogo: entry.logo_name,
    backgroundColor: entry.backgroundColor,
  };
}

function changePasswordCallback(tileClick) {
  tileClick.$store.dispatch('navigation/setActiveButton', '');
  tileClick.$store.dispatch('modal/setShowModalPromise', {
    name: 'ChangePassword',
    stubborn: true,
  }).then((values) => {
    tileClick.$store.dispatch('activateLoadingState');
    changePassword(values.oldPassword, values.newPassword).then((response) => {
      tileClick.$store.dispatch('notifications/addSuccessNotification', {
        title: _('Change password'),
        description: response.data.message,
      });
      tileClick.$store.dispatch('modal/hideAndClearModal');
      tileClick.$store.dispatch('deactivateLoadingState');
    }, (error) => {
      console.error('Error while changing password', error);
      tileClick.$store.dispatch('notifications/addErrorNotification', {
        title: _('Change password'),
      });
      tileClick.$store.dispatch('modal/hideAndClearModal');
      tileClick.$store.dispatch('deactivateLoadingState');
      return changePasswordCallback(tileClick);
    });
  }, () => {
    tileClick.$store.dispatch('deactivateLoadingState');
    tileClick.$store.dispatch('modal/hideAndClearModal');
  });
}

export default function createUserMenu(portalData) {
  if (!portalData) {
    return [];
  }
  const menuTitle = {
    de_DE: 'Benutzereinstellungen',
    en_US: 'User settings',
    fr_FR: 'Réglages utilisateur',
  };

  const userLinks = portalData.user_links;
  const availableTiles = portalData.entries;
  const { defaultLinkTarget } = portalData.portal;
  const subMenuItems = userLinks
    .map((entryID) => makeEntry(entryID, availableTiles, defaultLinkTarget))
    .filter((entry) => !!entry);

  if (portalData.username) {
    subMenuItems.unshift({
      id: `menu-item-${randomId()}`,
      title: {
        en_US: 'Change password',
        de_DE: 'Passwort ändern',
      },
      linkTarget: 'internalFunction',
      internalFunction: changePasswordCallback,
      links: [],
    });
  }

  const menuElement = {
    id: `menu-${randomId()}`,
    title: menuTitle,
    linkTarget: 'samewindow',
    subMenu: subMenuItems,
  };
  if (subMenuItems.length) {
    return menuElement;
  }
  return null;
}
