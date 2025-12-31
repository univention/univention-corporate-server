/*
  * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  * SPDX-License-Identifier: AGPL-3.0-only
 */
import { ActionContext } from 'vuex';
import { RootState } from '../../root.models';
import { Locale } from '../locale/locale.models';

export type LocalizedString = Record<Locale, string>;

export type LinkTarget = 'newwindow' | 'samewindow' | 'embedded' | 'function';

export type LinkTargetOrDefault = 'newwindow' | 'samewindow' | 'embedded' | 'function' | 'useportaldefault';

export interface PortalImageDataBlob {
  data: string,
}

export interface Link {
  locale: string,
  link: string,
}

export interface Tile {
  id: string,
  layoutId: string,
  dn: string,
  title: LocalizedString,
  isFolder: boolean,
}

export interface BaseTile extends Tile {
  allowedGroups: string[],
  activated: boolean,
  anonymous: boolean,
  selectedGroups: string[],
  backgroundColor: string | null,
  description: LocalizedString,
  keywords: LocalizedString,
  linkTarget: LinkTarget,
  target: string | null,
  originalLinkTarget: LinkTargetOrDefault,
  links: Link[],
  pathToLogo: string,
  key: any, // TODO: no idea how to type this object :(
}

export interface FolderTile extends Tile {
  tiles: BaseTile[]
}

export type TileOrFolder = BaseTile | FolderTile;

export interface Category {
  id: string,
  layoutId: string,
  title: LocalizedString,
  dn: string,
  virtual: boolean,
  tiles: TileOrFolder[],
}

export type PortalContent = [string, string[]][];

export interface PortalEntry {
  id: string,
  dn: string,
  activated: boolean,
  allowedGroups: string[],
  anonymous: boolean,
  backgroundColor: string | null,
  description: LocalizedString,
  keywords: LocalizedString,
  linkTarget: LinkTargetOrDefault,
  target: string | null,
  links: Link[],
  icon_url: string | null,
  name: LocalizedString,
}

export interface PortalFolder {
  id: string,
  dn: string,
  entries: string[],
  name: LocalizedString,
}

export interface PortalCategory {
  id: string,
  dn: string,
  entries: string[],
  virtual: boolean,
  display_name: LocalizedString,
}

export type PortalAnnouncementSeverity = null | 'info' | 'warn' | 'success' | 'danger'

export type PortalAnnouncement = {
  name: string;
  dn: string;
  allowedGroups: string[];
  isSticky: boolean;
  message: LocalizedString;
  needsConfirmation: boolean;
  severity: PortalAnnouncementSeverity;
  title: LocalizedString;
  visibleFrom: string | null;
  visibleUntil: string | null;
}

export interface Portal {
  name: LocalizedString;
  background: PortalImageDataBlob | null;
  defaultLinkTarget: LinkTarget,
  dn: string,
  categories: string[],
  logo: PortalImageDataBlob | null,
  showUmc: boolean,
  ensureLogin: boolean,
  content: PortalContent,
}

export interface PortalBaseLayout {
  layout: string[],
  categories: { [index: string]: string[] },
  folders: { [index: string]: string[] },
}

export interface PortalLayoutEntry {
  id: string,
  dn: string,
  tiles?: PortalLayoutEntry[],
}
export interface PortalLayoutCategory extends PortalLayoutEntry {
  tiles: PortalLayoutEntry[],
}
export type PortalLayout = PortalLayoutCategory[];

export interface PortalData {
  entries: PortalEntry[],
  folders: PortalFolder[],
  categories: PortalCategory[],
  userLinks: string[],
  menuLinks: string[],
  announcements: PortalAnnouncement[],
  portal: Portal,
  baseLayout: PortalBaseLayout,
  layout: PortalLayout,
}
export interface PortalDataState {
  portal: PortalData;
  editMode: boolean;
  cacheId: string;
  errorContentType: number | null;
}

export type Position = {
  categoryIdx: null | number;
  folderIdx: null | number;
  entryIdx: null | number;
  entryType: null | 'category' | 'tile';
  contextType: null | 'root' | 'category' | 'folder';
}

export type PortalDataActionContext = ActionContext<PortalDataState, RootState>;
