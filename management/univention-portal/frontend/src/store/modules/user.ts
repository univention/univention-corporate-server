import { Module } from 'vuex';

interface User {
  username: string;
  displayName: string;
  mayEditPortal: boolean;
  mayLoginViaSAML: boolean;
}

export interface State {
  user: User;
}

const user: Module<State, unknown> = {
  namespaced: true,
  state: {
    user: {
      username: '',
      displayName: '',
      mayEditPortal: false,
      mayLoginViaSAML: false,
    },
  },

  mutations: {
    SETUSER: (state, payload) => {
      state.user = payload.user;
    },
  },

  getters: {
    userState: (state) => state.user,
  },

  actions: {
    setUser({ commit }, payload) {
      commit('SETUSER', payload);
    },
  },
};

export default user;
