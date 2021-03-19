import { PortalModule } from '../types';

export interface MetaDataState {
  meta: Record<string, unknown>;
}

const metaData: PortalModule<MetaDataState> = {
  namespaced: true,
  state: {
    meta: {
      cookieBanner: {
        show: false,
        title: {
          en: '',
        },
        text: {
          en: '',
        },
      },
    },
  },

  mutations: {
    META(state, payload) {
      state.meta = payload;
    },
  },

  getters: {
    getMeta: (state) => state.meta,
  },

  actions: {
    setMeta({ commit }, payload) {
      commit('META', payload);
    },
  },
};

export default metaData;
