import { Module } from 'vuex';

export interface State {
  searchQuery: string,
}

const search: Module<State, unknown> = {
  namespaced: true,
  state: {
    searchQuery: '',
  },

  mutations: {
    SET_SEARCH_QUERY(state, payload) {
      state.searchQuery = payload;
    },
  },

  getters: {
    searchQuery: (state) => state.searchQuery,
  },

  actions: {
    setSearchQuery({ commit }, payload) {
      commit('SET_SEARCH_QUERY', payload);
    },
  },
};

export default search;
