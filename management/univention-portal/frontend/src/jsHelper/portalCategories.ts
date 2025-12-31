/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import {
  BaseTile,
  Category,
  FolderTile,
  LinkTarget,
  PortalCategory,
  PortalEntry,
  PortalFolder,
  PortalLayout,
  PortalLayoutEntry,
  TileOrFolder,
} from '@/store/modules/portalData/portalData.models';
import { localized } from '@/plugins/localize';

function isBaseTile(value: TileOrFolder | null): boolean {
  return !value?.isFolder;
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
      links: entry.links,
      linkTarget: entry.linkTarget === 'useportaldefault' ? defaultLinkTarget : entry.linkTarget,
      target: entry.target,
      originalLinkTarget: entry.linkTarget,
      pathToLogo: entry.icon_url || './questionMark.svg',
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
      tiles,
    };
  }
  console.warn('Not showing empty', entryItem.dn);
  return null;
}

export function doesTitleMatch(entry: TileOrFolder, searchQuery: string): boolean {
  return localized(entry.title)
    .toLowerCase()
    .includes(searchQuery.toLowerCase());
}

export function doesDescriptionMatch(entry: TileOrFolder, searchQuery: string): boolean {
  return !entry.isFolder && localized((entry as BaseTile).description)
    .toLowerCase()
    .includes(searchQuery.toLowerCase());
}

export function doesKeywordsMatch(entry: TileOrFolder, searchQuery: string): boolean {
  return !entry.isFolder && localized((entry as BaseTile).keywords)
    .toLowerCase()
    .includes(searchQuery.toLowerCase());
}

export function doesFolderMatch(entry: TileOrFolder, searchQuery: string): boolean {
  return entry.isFolder && (entry as FolderTile).tiles.some((t) => doesTitleMatch(t, searchQuery) || doesDescriptionMatch(t, searchQuery) || doesKeywordsMatch(t, searchQuery));
}

export function createCategories(
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
