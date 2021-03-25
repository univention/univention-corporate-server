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
export type Locale = 'en' | 'en_US' | 'de_DE' | 'fr_FR';

export type Title = Record<Locale, string>;

export type Description = Record<Locale, string>;

export type LinkTarget = 'newwindow' | 'samewindow' | 'embedded' | 'function';

export interface Tile {
  id: string,
  title: Title,
  isFolder: boolean
}

export interface BaseTile extends Tile {
  description: Record<Locale, string>,
  linkTarget: LinkTarget,
  links: string[],
  pathToLogo: string,
}

export interface FolderTile extends Tile {
  tiles: BaseTile[]
}

export interface Category {
  title: Record<Locale, string>,
  tiles: Tile[],
}

export interface Notification {
  bubbleTitle: string;
  bubbleDescription: string;
  onClick: () => void | null;
}

export interface WeightedNotification extends Notification {
  bubbleImportance: string;
}

export interface FullNotification extends WeightedNotification {
  bubbleToken: string;
}

export interface Portal {
  name: Record<string, string>;
  background: string | null;
}

export interface PortalData {
  portal: Portal;
}

export interface Tab {
  tabLabel: string,
  ariaLabel: string,
  closeIcon: string,
  logo: string,
  iframeLink: string
}

export interface Tooltip {
  title: string | null,
  icon: string | null,
  description: string,
  ariaId: string,
}

export interface User {
  username: string;
  displayName: string;
  mayEditPortal: boolean;
  mayLoginViaSAML: boolean;
}

