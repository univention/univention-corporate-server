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

import { BaseTile, Category, LinkTarget, PortalCategory, PortalContent, PortalEntry, PortalFolder, TileOrFolder } from '@/store/modules/portalData/portalData.models';
import { randomId } from '@/jsHelper/tools';

function isBaseTile(value: any): value is BaseTile {
  return (value !== null) && !value.isFolder;
}

function makeEntry(
  entryID: string,
  portalEntries: PortalEntry[],
  portalFolders: PortalFolder[],
  defaultLinkTarget: LinkTarget,
  editMode: boolean,
): TileOrFolder | null {
  const entry = portalEntries.find((data) => data.dn === entryID);
  if (entry) {
    // TODO: remove id once the service is offering the right data.
    return {
      id: entry.id,
      dn: entry.dn,
      title: entry.name,
      isFolder: false,
      activated: entry.activated,
      anonymous: entry.anonymous,
      allowedGroups: entry.allowedGroups,
      selectedGroups: [], // needed for storing selected groups
      backgroundColor: entry.backgroundColor,
      description: entry.description,
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
  const folder = portalFolders.find((data) => data.dn === entryID);
  if (!folder) {
    return null;
  }
  const tiles: BaseTile[] = [];
  folder.entries.forEach((folderEntryID) => {
    const entryInFolder = makeEntry(folderEntryID, portalEntries, portalFolders, defaultLinkTarget, editMode);
    if (isBaseTile(entryInFolder)) {
      tiles.push(entryInFolder);
    } else {
      console.warn('Entry', folderEntryID, 'not found!');
    }
  });
  if (tiles.length || editMode) {
    return {
      id: folder.id,
      dn: folder.dn,
      title: folder.name,
      isFolder: true,
      tiles,
    };
  }
  console.warn('Not showing empty', entryID);
  return null;
}

export default function createCategories(
  portalContent: PortalContent,
  portalCategories: PortalCategory[],
  portalEntries: PortalEntry[],
  portalFolders: PortalFolder[],
  defaultLinkTarget: LinkTarget,
  editMode: boolean,
): Category[] {
  const ret: Category[] = [];
  portalContent.forEach(([categoryID, categoryEntries]) => {
    const category = portalCategories.find((cat) => cat.dn === categoryID);
    if (!category) {
      console.warn('Category', categoryID, 'not found!');
      return;
    }
    const tiles: TileOrFolder[] = [];
    categoryEntries.forEach((entryID) => {
      const entry = makeEntry(entryID, portalEntries, portalFolders, defaultLinkTarget, editMode);
      if (!entry) {
        return;
      }
      tiles.push(entry);
    });
    if (tiles.length || editMode) {
      const categoryItem = {
        id: category.id,
        title: category.display_name,
        dn: category.dn,
        virtual: category.virtual,
        tiles,
      };
      ret.push(categoryItem);
    } else {
      console.warn('Not showing empty', categoryID);
    }
  });
  return ret;
}
