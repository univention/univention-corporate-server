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
// vue
import axios from 'axios';
import { InjectionKey } from 'vue';
import { createStore, Store, useStore as baseUseStore } from 'vuex';
// modules
import tooltip from '@/store/modules/tooltip';
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
    tooltip,
    user,
  },
  strict: process.env.NODE_ENV !== 'production',
  state: {
    // Just a sample property, the RootState should not be empty
    version: '1.0.0',
  },
  mutations: {},
  actions: {
    loadPortal: ({ dispatch }, payload) => new Promise((resolve, reject) => {
      console.log('Loading Portal...');

      // Get portal data
      const headers = {};
      if (payload.adminMode) {
        console.log('... in Admin mode');
        headers['X-Univention-Portal-Admin-Mode'] = 'yes';
      }
      const portalRequest = axios.get(`${portalUrl}${portalJsonPath}`, { headers });
      const portalPromises = [
        `${portalUrl}${portalMetaPath}`, // Get meta data
        `${portalUrl}${languageJsonPath}`, // Get locale data
      ].map((url) => axios.get(url));
      portalPromises.push(portalRequest);

      axios.all(portalPromises).then(axios.spread((metaResponse, languageResponse, portalResponse) => {
        const [meta, availableLocales, portal] = [metaResponse.data, languageResponse.data, portalResponse.data];
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
