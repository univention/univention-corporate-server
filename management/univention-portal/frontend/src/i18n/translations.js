// get default dictionary
import { catalog } from '@/assets/data/dictionary';
import axios from 'axios';

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

export { catalog, updateLocale };
