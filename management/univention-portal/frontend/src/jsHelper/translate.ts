/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { getCurrentCatalog } from '@/i18n/translations';

const replaceKeys = (translationString: string, variables: Record<string, string>): string => {
  const replaced = translationString.replace(/\%\((.*?)\)s/g, (match, placeHolder) => variables[placeHolder]);
  return replaced;
};

function _(translationString: string, variables?: Record<string, string>): string {
  let catalog: Record<string, string> = {};
  catalog = getCurrentCatalog();
  const translatedString = catalog[translationString] || translationString;
  return variables ? replaceKeys(translatedString, variables) : translatedString;
}

export { _ as default };
