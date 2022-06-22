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

function makeEntry(entryID, availableTiles, availableFolders, defaultLinkTarget) {
  let entry = availableTiles.find((tile) => tile.dn === entryID);
  if (entry) {
    return {
      id: `menu-item-${randomId()}`,
      title: entry.name,
      description: entry.description,
      links: entry.links,
      linkTarget: entry.linkTarget === 'useportaldefault' ? defaultLinkTarget : entry.linkTarget,
      target: entry.target,
      pathToLogo: entry.logo_name,
      backgroundColor: entry.backgroundColor,
    };
  }
  entry = availableFolders.find((folder) => folder.dn === entryID);
  return {
    id: `menu-${randomId()}`,
    title: entry.name,
    subMenu: entry.entries.map((folderEntryID) => makeEntry(folderEntryID, availableTiles, availableFolders, defaultLinkTarget)),
  };
}

export default function createMenuStructure(portalData) {
  if (!portalData) {
    return [];
  }
  const portalMenuLinks = portalData.menu_links;
  const availableTiles = portalData.entries;
  const availableFolders = portalData.folders;
  const { defaultLinkTarget } = portalData.portal;

  return portalMenuLinks.map((menuID) => makeEntry(menuID, availableTiles, availableFolders, defaultLinkTarget));
}
