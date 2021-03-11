import { Module } from 'vuex';

export interface State {
  meta: Record<string, unknown>;
}

const meta: Module<State, unknown> = {
  namespaced: true,
  state: {
    meta: {},
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
