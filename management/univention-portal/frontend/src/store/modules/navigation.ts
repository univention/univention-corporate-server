import { Module } from 'vuex';

export interface State {
  activeButton: string;
}

const navigation: Module<State, unknown> = {
  namespaced: true,
  state: {
    activeButton: '',
  },

  mutations: {
    ACTIVEBUTTON(state, id) {
      state.activeButton = id;
    },
  },

  getters: {
    getActiveButton: (state) => state.activeButton,
  },

  actions: {
    setActiveButton({ commit }, id) {
      commit('ACTIVEBUTTON', id);
    },
  },
};

export default navigation;
