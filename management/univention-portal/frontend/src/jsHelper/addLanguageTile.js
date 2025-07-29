/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { randomId } from '@/jsHelper/tools';

export default function addLanguageTile(portalLanguageData) {
  if (portalLanguageData.length < 2) {
    return null;
  }
  const menuTitle = {
    de_DE: 'Sprache ändern',
    en_US: 'Change Language',
    fr_FR: 'Changer de langue',
  };

  const subMenuItems = portalLanguageData.map((element) => ({
    id: `menu-item-language-${element.id}`,
    title: { en_US: element.label },
    linkTarget: 'internalFunction',
    internalFunction: (tileClick) => {
      tileClick.$store.dispatch('locale/setLocale', element.id.replace('-', '_'));
      return false;
    },
    links: [],
  }));

  const menuElement = {
    id: `menu-${randomId()}`,
    title: menuTitle,
    linkTarget: 'samewindow',
    subMenu: subMenuItems,
  };
  return menuElement;
}
