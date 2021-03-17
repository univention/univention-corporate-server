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

export interface User {
  username: string;
  displayName: string;
  mayEditPortal: boolean;
  mayLoginViaSAML: boolean;
}
