// vue
import axios from 'axios';
import { InjectionKey } from 'vue';
import { createStore, Store, useStore as baseUseStore } from 'vuex';
// modules
import categories from './modules/categories';
import locale from './modules/locale';
import menu from './modules/menu';
import metaData from './modules/metaData';
import modal from './modules/modal';
import navigation from './modules/navigation';
import notificationBubble from './modules/notificationBubble';
import portalData from './modules/portalData';
import search from './modules/search';
import tabs from './modules/tabs';
import user from './modules/user';
import { RootState } from './types';

// get env vars
const portalUrl = process.env.VUE_APP_PORTAL_URL || '';
const languageJsonPath = process.env.VUE_APP_LANGUAGE_DATA || '/univention/languages.json';
const portalJsonPath = process.env.VUE_APP_PORTAL_DATA || './portal.json';
const portalMetaPath = process.env.VUE_APP_META_DATA || '/univention/meta.json';

export const key: InjectionKey<Store<RootState>> = Symbol('');

export const store = createStore<RootState>({
  modules: {
    categories,
    locale,
    menu,
    metaData,
    modal,
    navigation,
    notificationBubble,
    portalData,
    search,
    tabs,
    user,
  },
  strict: process.env.NODE_ENV !== 'production',
  state: {
    // Just a sample property, the RootState should not be empty
    version: '1.0.0',
  },
  mutations: {},
  actions: {
    loadPortal: ({ dispatch }) => new Promise((resolve, reject) => {
      console.log('Loading Portal...');

      const portalPromises = [
        `${portalUrl}${portalMetaPath}`, // Get meta data
        `${portalUrl}${portalJsonPath}`, // Get portal data
        `${portalUrl}${languageJsonPath}`, // Get locale data
      ].map((url) => axios.get(url));

      axios.all(portalPromises).then(axios.spread((metaResponse, portalResponse, languageResponse) => {
        const [meta, portal, availableLocales] = [metaResponse.data, portalResponse.data, languageResponse.data];
        dispatch('metaData/setMeta', meta);
        dispatch('menu/setMenu', { portal, availableLocales });
        dispatch('portalData/setPortal', portal);
        dispatch('categories/setOriginalArray', portal);
        dispatch('user/setUser', {
          user: {
            username: portal.username,
            displayName: portal.user_displayname,
            mayEditPortal: portal.may_edit_portal,
            mayLoginViaSAML: portal.may_login_via_saml,
          },
        });
        resolve(portal);
      }), (error) => {
        reject(error);
      });
    }),
  },
  getters: {},
});

// Define your own `useStore` composition function
export function useStore(): Store<RootState> {
  return baseUseStore(key);
}
