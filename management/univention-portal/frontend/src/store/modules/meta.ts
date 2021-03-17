import { PortalModule } from '../types';

export interface ModuleState {
  meta: Record<string, unknown>;
}

const meta: PortalModule<ModuleState> = {
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

export default meta;
