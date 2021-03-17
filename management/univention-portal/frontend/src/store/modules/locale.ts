import { updateLocale } from '@/i18n/translations';
import { Locale } from '../models';
import { PortalModule } from '../types';

export interface LocaleState {
  locale: Locale;
}

const locale: PortalModule<LocaleState> = {
  namespaced: true,
  state: {
    locale: 'en_US',
  },

  mutations: {
    NEWLOCALE(state, payload) {
      state.locale = payload;
    },
  },

  getters: {
    getLocale: (state) => state.locale,
  },

  actions: {
    setLocale({ commit }, payload: Locale) {
      commit('NEWLOCALE', payload);
      const localePrefix = payload.slice(0, 2);
      return updateLocale(localePrefix);
    },
  },
};

export default locale;
