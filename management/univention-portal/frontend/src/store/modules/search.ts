import { PortalModule } from '../types';

export interface SearchState {
  searchQuery: string,
}

const search: PortalModule<SearchState> = {
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
