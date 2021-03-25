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
import axios from 'axios';

// get default dictionary
import { catalog } from '@/assets/data/dictionary';

// get env vars
const portalUrl = process.env.VUE_APP_PORTAL_URL || '';

const translationCatalogs = {};

function getCatalog(locale) {
  return new Promise((resolve, reject) => {
    if (locale in translationCatalogs) {
      const translationCatalog = translationCatalogs[locale];
      if (translationCatalog) {
        resolve(translationCatalog);
      } else {
        reject();
      }
    } else {
      axios.get(`${portalUrl}i18n/${locale}.json`).then(
        (response) => {
          const translationCatalog = response.data;
          translationCatalogs[locale] = translationCatalog;
          resolve(translationCatalog);
        },
        () => {
          // no locale found (404?)
          translationCatalogs[locale] = null;
          reject();
        },
      );
    }
  });
}

async function updateLocale(locale) {
  return getCatalog(locale).then(
    (translationCatalog) => {
      Object.keys(catalog).forEach((key) => {
        const value = catalog[key];
        if (translationCatalog && value.original in translationCatalog) {
          const translatedValue = translationCatalog[value.original];
          value.translated.value = translatedValue;
        } else {
          value.translated.value = value.original;
        }
      });
    },
    () => {
      // no locale found (404?)
      Object.keys(catalog).forEach((key) => {
        const value = catalog[key];
        value.translated.value = value.original; // Vuex error: Do not mutate store state outside mutation handlers
      });
    },
  );
}

function translate(key) {
  return catalog[key].translated.value;
}

export { catalog, updateLocale, translate };
