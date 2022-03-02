/*
  * Copyright 2021-2022 Univention GmbH
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
import { getAdminState } from '@/jsHelper/admin';
import activity from './modules/activity';
import dragndrop from './modules/dragndrop';
import locale from './modules/locale';
import menu from './modules/menu';
import metaData from './modules/metaData';
import navigation from './modules/navigation';
import modal from './modules/modal';
import notifications from './modules/notifications';
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

const mutations = {
  SET_LOADING_STATE(state, active: boolean) {
    state.loadingState = active;
  },
};

const getters = {
  getLoadingState: (state) => state.loadingState,
};

const actions = {
  activateLoadingState({ commit }) {
    commit('SET_LOADING_STATE', true);
  },
  deactivateLoadingState({ commit }) {
    commit('SET_LOADING_STATE', false);
  },
  portalJsonRequest: (_, payload) => {
    const umcLang = getCookie('UMCLang');
    const headers = {
      'X-Requested-With': 'XMLHTTPRequest',
      'Accept-Language': umcLang || 'en-US',
    };
    if (payload.adminMode || getAdminState()) {
      headers['X-Univention-Portal-Admin-Mode'] = 'yes';

      if (process.env.VUE_APP_LOCAL) {
        return axios.get(`${portalUrl}dev-${portalJsonPath}`, { headers });
      }
    }
    return axios.get(`${portalUrl}${portalJsonPath}`, { headers });
  },
  loadPortal: ({ dispatch }, payload) => new Promise((resolve, reject) => {
    // Get portal data
    const portalRequest = dispatch('portalJsonRequest', payload)
      .catch((error) => error);
    const portalPromises = [
      `${portalUrl}${portalMetaPath}`, // Get meta data
      `${portalUrl}${languageJsonPath}`, // Get locale data
    ].map((url) => axios.get(url).catch((error) => error));
    portalPromises.push(portalRequest);

    Promise.all(portalPromises).then(async ([metaResponse, languageResponse, portalResponse]) => {
      const [meta, availableLocales, portal] = [metaResponse.data, languageResponse.data, portalResponse.data];
      if (languageResponse.isAxiosError) {
        console.warn(`Failed to fetch ${portalUrl}${languageJsonPath}`);
      } else {
        await dispatch('locale/setAvailableLocale', availableLocales);
      }
      if (metaResponse.isAxiosError) {
        console.warn(`Failed to fetch ${portalUrl}${portalMetaPath}`, metaResponse);
      } else {
        dispatch('metaData/setMeta', meta);
      }

      dispatch('menu/setMenu', {
        portal,
        availableLocales: availableLocales ?? [],
      });
      if (portalResponse.isAxiosError) {
        console.warn(`Failed to fetch ${portalUrl}${portalJsonPath}`);
        dispatch('portalData/setPortalErrorDisplay', 502);
        dispatch('deactivateLoadingState');
      } else {
        dispatch('portalData/setPortal', { portal, adminMode: payload.adminMode || getAdminState() });
        dispatch('user/setUser', {
          user: {
            username: portal.username,
            displayName: portal.user_displayname,
            mayEditPortal: portal.may_edit_portal,
            authMode: portal.auth_mode,
          },
        });
        resolve(portal);
      }
    })
      .catch((error) => {
        // We won't get here at the moment because we call .catch on
        // all promises in Promise.all
        dispatch('portalData/setPortalErrorDisplay', 502);
        dispatch('deactivateLoadingState');
        reject(error);
      });
  }),
};

export const store = createStore<RootState>({
  strict: process.env.NODE_ENV !== 'production',
  state: initialRootState,
  mutations,
  actions,
  getters,
  modules: {
    activity,
    dragndrop,
    locale,
    menu,
    metaData,
    modal,
    navigation,
    notifications,
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
