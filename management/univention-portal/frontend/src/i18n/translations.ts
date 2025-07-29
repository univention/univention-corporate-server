/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { reactive } from 'vue';

import axios from 'axios';
import { ShortLocale } from '@/store/modules/locale/locale.models';

interface TranslationCatalogDefinition {
  [key: string]: Record<string, string>;
}
const translationCatalogs: TranslationCatalogDefinition = {};

const currentCatalog = reactive({});

function getCatalog(locale: ShortLocale): Promise<Record<string, string>> {
  return new Promise((resolve, reject) => {
    if (locale in translationCatalogs) {
      const translationCatalog = translationCatalogs[locale];
      if (translationCatalog) {
        resolve(translationCatalog);
      } else {
        reject();
      }
    } else {
      axios.get(`./i18n/${locale}.json`).then(
        (response) => {
          const translationCatalog = response.data;
          translationCatalogs[locale] = translationCatalog;
          resolve(translationCatalog);
        },
        () => {
          reject();
        },
      );
    }
  });
}

async function updateLocale(locale: ShortLocale): Promise<unknown> {
  return getCatalog(locale).then(
    (translationCatalog) => {
      Object.keys(currentCatalog).forEach((key) => delete currentCatalog[key]);
      Object.entries(translationCatalog).forEach(([key, value]) => {
        currentCatalog[key] = value;
      });
      return translationCatalog;
    },
    () => {
      Object.keys(currentCatalog).forEach((key) => delete currentCatalog[key]);
      // no locale found (404?)
      // console.error('404: No translation file found.');
    },
  );
}

function getCurrentCatalog(): Record<string, string> {
  return currentCatalog;
}

export { updateLocale, getCurrentCatalog };
