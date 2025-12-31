/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
    target: entry.target,
    pathToLogo: entry.icon_url,
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
