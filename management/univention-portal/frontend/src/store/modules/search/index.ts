/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { Commit } from 'vuex';
import _ from '@/jsHelper/translate';
import { PortalModule } from '@/store/root.models';
import { SearchQuery } from './search.models';

export interface SearchState {
  searchQuery: string,
}

const search: PortalModule<SearchState> = {
  namespaced: true,
  state: {
    searchQuery: '',
  },

  mutations: {
    SET_SEARCH_QUERY(state: SearchState, payload: SearchQuery): void {
      state.searchQuery = payload;
    },
  },

  getters: {
    searchQuery: (state) => state.searchQuery,
  },

  actions: {
    setSearchQuery({ commit }: { commit: Commit }, payload: SearchQuery): void {
      commit('SET_SEARCH_QUERY', payload);
    },
  },
};

export default search;
