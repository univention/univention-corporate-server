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
import { Locale } from '../locale/locale.models';

export type Title = Record<Locale, string>;

export type Description = Record<Locale, string>;

export type LinkTarget = 'newwindow' | 'samewindow' | 'embedded' | 'function';

export type LinkTargetOrDefault = 'newwindow' | 'samewindow' | 'embedded' | 'function' | 'useportaldefault';

export interface Link {
  locale: Locale,
  link: string,
}

export interface Tile {
  id: string,
  layoutId: string,
  dn: string,
  title: Title,
  isFolder: boolean,
}

export interface BaseTile extends Tile {
  allowedGroups: string[],
  activated: boolean,
  anonymous: boolean,
  selectedGroups: string[],
  backgroundColor: string | null,
  description: Description,
  linkTarget: LinkTarget,
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
  title: Record<Locale, string>,
  dn: string,
  virtual: boolean,
  tiles: TileOrFolder[],
}

export type LocalizedString = Record<string, string>;

export type PortalContent = [string, string[]][];

export interface PortalEntry {
  id: string,
  dn: string,
  activated: boolean,
  allowedGroups: string[],
  anonymous: boolean,
  backgroundColor: string | null,
  description: Description,
  linkTarget: LinkTargetOrDefault,
  links: Link[],
  logo_name: string | null,
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
  categories: {[index:string]: string[]},
  folders: {[index:string]: string[]},
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
  portal: Portal;
  baseLayout: PortalBaseLayout,
  layout: PortalLayout,
}

export interface PortalImageDataBlob {
  data: string,
}
