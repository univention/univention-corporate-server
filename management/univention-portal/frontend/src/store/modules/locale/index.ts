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
import { ActionContext, Dispatch } from 'vuex';
import { updateLocale } from '@/i18n/translations';
import { getCookie, setCookie } from '@/jsHelper/tools';
import { PortalModule, RootState } from '@/store/root.models';
import { Locale, ShortLocale, LocaleDefinition } from './locale.models';

type LocaleLabels = Partial<Record<Locale, string>>;
export interface LocaleState {
  locale: Locale;
  defaultLocale: Locale | null;
  availableLocales: Locale[];
  localeLabels: LocaleLabels;
}
type LocaleActionContext = ActionContext<LocaleState, RootState>;

const locale: PortalModule<LocaleState> = {
  namespaced: true,
  state: {
    locale: 'en_US',
    defaultLocale: null,
    availableLocales: ['en_US'],
    localeLabels: {},
  },

  mutations: {
    NEWLOCALE(state: LocaleState, payload: Locale): void {
      state.locale = payload;
    },
    DEFAULT_LOCALE(state: LocaleState, payload: Locale): void {
      state.defaultLocale = payload;
    },
    AVAILABLE_LOCALES(state: LocaleState, payload: Locale[]): void {
      state.availableLocales = payload;
    },
    LOCALE_LABELS(state: LocaleState, payload: LocaleLabels): void {
      state.localeLabels = payload;
    },
  },

  getters: {
    getLocale: (state: LocaleState) => state.locale,
    getDefaultLocale: (state: LocaleState) => state.defaultLocale,
    getAvailableLocales: (state: LocaleState) => state.availableLocales,
    getLocaleLabels: (state: LocaleState) => state.localeLabels,
  },

  actions: {
    setLocale({ commit, dispatch }: LocaleActionContext, payload: Locale): Promise<unknown> {
      commit('NEWLOCALE', payload);
      const lang = payload.replace('_', '-');
      dispatch('menu/setDisabled', [`menu-item-language-${lang}`], { root: true });
      setCookie('UMCLang', lang);
      const localePrefix = payload.slice(0, 2);
      // TODO create helper function
      const html = document.documentElement;
      html.setAttribute('lang', localePrefix);
      return updateLocale(localePrefix as ShortLocale);
    },
    setInitialLocale({ getters, dispatch }: LocaleActionContext): Promise<Dispatch> {
      if (getters.getAvailableLocales.length === 1) {
        dispatch('setLocale', getters.getAvailableLocales[0]);
      }
      const umcLang = getCookie('UMCLang');
      if (umcLang) {
        return dispatch('setLocale', umcLang.replace('-', '_'));
      }
      if (getters.getDefaultLocale) {
        return dispatch('setLocale', getters.getDefaultLocale);
      }
      if (window.navigator.languages) {
        let preferred = null;
        window.navigator.languages.some((language) => {
          preferred = getters.getAvailableLocales.find((loc) => loc === language.replace('-', '_') || loc.slice(0, 2) === language);
          return !!preferred;
        });
        if (preferred) {
          return dispatch('setLocale', preferred);
        }
      }
      return dispatch('setLocale', 'en_US');
    },
    setAvailableLocale({ dispatch, commit }: LocaleActionContext, payload: LocaleDefinition[]): Promise<Dispatch> {
      const locales = payload
        .map((loc) => loc.id.replace('-', '_'))
        // sort locales alphabetically but put en_US at the front
        .sort((a, b) => {
          if (a === 'en_US') {
            return -1;
          }
          if (b === 'en_US') {
            return 1;
          }
          return a < b ? -1 : 1;
        });
      commit('AVAILABLE_LOCALES', locales);

      const localeLabels = payload.reduce((dict: LocaleLabels, loc) => {
        const lang = loc.id.replace('-', '_');
        dict[lang] = `${loc.label} (${lang})`;
        return dict;
      }, {});
      commit('LOCALE_LABELS', localeLabels);

      const defaultLocale = payload.find((loc) => loc.default);
      if (defaultLocale) {
        commit('DEFAULT_LOCALE', defaultLocale.id.replace('-', '_'));
      }
      // TODO create helper function
      const html = document.documentElement;
      html.setAttribute('lang', 'en'); // setting document lang to en, because it is also set in line 47, 48
      return dispatch('setInitialLocale');
    },
  },
};

export default locale;
