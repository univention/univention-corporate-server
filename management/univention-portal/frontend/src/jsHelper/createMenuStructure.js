/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
      pathToLogo: entry.icon_url,
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
