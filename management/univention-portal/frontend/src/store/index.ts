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
// modules
import axios from 'axios';
import { InjectionKey } from 'vue';
import { createStore, Store, useStore as baseUseStore } from 'vuex';
import { getCookie } from '@/jsHelper/tools';
import locale from './modules/locale';
import menu from './modules/menu';
import metaData from './modules/metaData';
import modal from './modules/modal';
import navigation from './modules/navigation';
import notificationBubble from './modules/notificationBubble';
import portalData from './modules/portalData';
import search from './modules/search';
import tabs from './modules/tabs';
import tooltip from './modules/tooltip';
import user from './modules/user';
import { initialRootState, RootState } from './root.models';

// get env vars
const portalUrl = process.env.VUE_APP_PORTAL_URL || '';
const languageJsonPath = process.env.VUE_APP_LANGUAGE_DATA || '/univention/languages.json';
const portalJsonPath = process.env.VUE_APP_PORTAL_DATA || './portal.json';
const portalMetaPath = process.env.VUE_APP_META_DATA || '/univention/meta.json';

export const key: InjectionKey<Store<RootState>> = Symbol('');

const actions = {
  activateLoadingState({ dispatch }) {
    dispatch('modal/setAndShowModal', {
      name: 'LoadingOverlay',
    });
  },
  deactivateLoadingState({ dispatch }) {
    dispatch('modal/hideAndClearModal');
  },
  portalJsonRequest: (_, payload) => {
    console.log('Loading Portal...');
    const umcLang = getCookie('UMCLang');
    const headers = {
      'X-Requested-With': 'XMLHTTPRequest',
      'Accept-Language': umcLang || 'en-US',
    };
    if (payload.adminMode) {
      console.log('... in Admin mode');
      headers['X-Univention-Portal-Admin-Mode'] = 'yes';

      if (process.env.VUE_APP_LOCAL) {
        return axios.get(`${portalUrl}dev-${portalJsonPath}`, { headers });
      }
    }
    return axios.get(`${portalUrl}${portalJsonPath}`, { headers });
  },
  loadPortal: ({ dispatch }, payload) => new Promise((resolve, reject) => {
    // Get portal data
    const portalRequest = dispatch('portalJsonRequest', payload);
    const portalPromises = [
      `${portalUrl}${portalMetaPath}`, // Get meta data
      `${portalUrl}${languageJsonPath}`, // Get locale data
    ].map((url) => axios.get(url));
    portalPromises.push(portalRequest);

    axios.all(portalPromises).then(axios.spread((metaResponse, languageResponse, portalResponse) => {
      const [meta, availableLocales, portal] = [metaResponse.data, languageResponse.data, portalResponse.data];
      dispatch('locale/setAvailableLocale', availableLocales);
      dispatch('metaData/setMeta', meta);
      dispatch('menu/setMenu', { portal, availableLocales });
      dispatch('portalData/setPortal', portal);
      dispatch('user/setUser', {
        user: {
          username: portal.username,
          displayName: portal.user_displayname,
          mayEditPortal: portal.may_edit_portal,
          authMode: portal.auth_mode,
        },
      });
      resolve(portal);
    }), (error) => {
      reject(error);
    });
  }),
};

export const store = createStore<RootState>({
  strict: process.env.NODE_ENV !== 'production',
  state: initialRootState,
  actions,
  modules: {
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
});

// Define your own `useStore` composition function
export function useStore(): Store<RootState> {
  return baseUseStore(key);
}
