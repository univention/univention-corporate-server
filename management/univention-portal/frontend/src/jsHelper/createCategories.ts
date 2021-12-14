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

import {
  BaseTile,
  Category,
  LinkTarget,
  PortalCategory,
  PortalEntry,
  PortalFolder,
  PortalLayout,
  PortalLayoutEntry,
  TileOrFolder,
} from '@/store/modules/portalData/portalData.models';

function isBaseTile(value: any): value is BaseTile {
  return (value !== null) && !value.isFolder;
}

function makeEntry(
  entryItem: PortalLayoutEntry,
  portalEntries: PortalEntry[],
  portalFolders: PortalFolder[],
  defaultLinkTarget: LinkTarget,
  editMode: boolean,
): TileOrFolder | null {
  const entry = portalEntries.find((data) => data.dn === entryItem.dn);
  if (entry) {
    // TODO: remove id once the service is offering the right data.
    return {
      id: entryItem.id,
      layoutId: entryItem.id,
      dn: entry.dn,
      title: entry.name,
      isFolder: false,
      activated: entry.activated,
      anonymous: entry.anonymous,
      allowedGroups: entry.allowedGroups,
      selectedGroups: [], // needed for storing selected groups
      backgroundColor: entry.backgroundColor,
      description: entry.description,
      keywords: entry.keywords,
      auth_info: entry.auth_info,
      links: entry.links,
      linkTarget: entry.linkTarget === 'useportaldefault' ? defaultLinkTarget : entry.linkTarget,
      originalLinkTarget: entry.linkTarget,
      pathToLogo: entry.logo_name || './questionMark.svg',
      key: {
        de_DE: 'de_DE',
        en_US: 'en_US',
      },
    };
  }
  const folder = portalFolders.find((data) => data.dn === entryItem.dn);
  if (!folder) {
    return null;
  }

  const tiles = (entryItem.tiles as PortalLayoutEntry[])
    .map((folderEntryItem) => {
      const entryInFolder = makeEntry(folderEntryItem, portalEntries, portalFolders, defaultLinkTarget, editMode);
      if (!isBaseTile(entryInFolder)) {
        console.warn('Entry', folderEntryItem.dn, 'not found!');
      }
      return entryInFolder;
    })
    .filter((folderEntry) => folderEntry !== null) as BaseTile[];
  if (tiles.length || editMode) {
    return {
      id: entryItem.id,
      layoutId: entryItem.id,
      dn: folder.dn,
      title: folder.name,
      isFolder: true,
      auth_info: {
        roles: [],
        idps: [],
        loa: 'low',
        disallow_anonymous: true,
        allow_global_search: false,
      },
      tiles,
    };
  }
  console.warn('Not showing empty', entryItem.dn);
  return null;
}

export default function createCategories(
  portalLayout: PortalLayout,
  portalCategories: PortalCategory[],
  portalEntries: PortalEntry[],
  portalFolders: PortalFolder[],
  defaultLinkTarget: LinkTarget,
  editMode: boolean,
): Category[] {
  const ret: Category[] = [];
  portalLayout.forEach((categoryItem) => {
    const category = portalCategories.find((cat) => cat.dn === categoryItem.dn);
    if (!category) {
      console.warn('Category', categoryItem.dn, 'not found!');
      return;
    }

    const tiles = categoryItem.tiles
      .map((entryItem) => makeEntry(entryItem, portalEntries, portalFolders, defaultLinkTarget, editMode))
      .filter((entry) => entry !== null) as TileOrFolder[];
    if (tiles.length || editMode) {
      ret.push({
        id: categoryItem.id,
        layoutId: categoryItem.id,
        title: category.display_name,
        dn: category.dn,
        virtual: category.virtual,
        tiles,
      });
    } else {
      console.warn('Not showing empty', categoryItem.dn);
    }
  });
  return ret;
}
