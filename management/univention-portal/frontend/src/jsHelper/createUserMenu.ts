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
