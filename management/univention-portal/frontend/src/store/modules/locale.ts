import { updateLocale } from '@/i18n/translations';
import { Module } from 'vuex';

export interface State {
  locale: string;
}

const locale: Module<State, unknown> = {
  namespaced: true,
  state: {
    locale: 'en_US',
  },

  mutations: {
    NEWLOCALE(state, payload) {
      state.locale = payload.locale;
    },
  },

  getters: {
    getLocale: (state) => state.locale,
  },

  actions: {
    setLocale({ commit }, payload) {
      commit('NEWLOCALE', payload);
      return updateLocale(payload.locale);
    },
  },
};

export default locale;
