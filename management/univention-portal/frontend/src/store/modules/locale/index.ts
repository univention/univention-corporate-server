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
import { updateLocale } from '@/i18n/translations';
import { setCookie } from '@/jsHelper/tools';
import { PortalModule } from '@/store/root.models';
import { Locale } from './locale.models';

interface LocaleDefinition {
  id: string;
  label: string;
}

export interface LocaleState {
  locale: Locale;
  availableLocales: Locale[];
}

const locale: PortalModule<LocaleState> = {
  namespaced: true,
  state: {
    locale: 'en_US',
    availableLocales: ['en_US'],
  },

  mutations: {
    NEWLOCALE(state, payload) {
      state.locale = payload;
    },
    AVAILABLE_LOCALES(state, payload) {
      state.availableLocales = payload;
    },
  },

  getters: {
    getLocale: (state) => state.locale,
    getAvailableLocales: (state) => state.availableLocales,
  },

  actions: {
    setLocale({ commit }, payload: Locale) {
      commit('NEWLOCALE', payload);
      setCookie('UMCLang', payload.replace('_', '-'));
      const localePrefix = payload.slice(0, 2);
      // TODO create helper function
      const html = document.documentElement;
      html.setAttribute('lang', localePrefix);
      return updateLocale(localePrefix);
    },
    setAvailableLocale({ commit }, payload: LocaleDefinition[]) {
      const locales = payload.map((loc) => loc.id.replace('-', '_'));
      commit('AVAILABLE_LOCALES', locales);
      // TODO create helper function
      const html = document.documentElement;
      html.setAttribute('lang', 'en'); // setting document lang to en, because it is also set in line 47, 48
    },
  },
};

export default locale;
