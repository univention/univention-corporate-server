import createCategories from '@/jsHelper/createCategories';
import { Module } from 'vuex';

export interface State {
  categories: Array<unknown>;
}

const categories: Module<State, unknown> = {
  namespaced: true,
  state: {
    categories: [],
  },

  mutations: {
    DEV_EMPTY(state) {
      state.categories = [];
    },
    REPLACE(state, payload) {
      state.categories = payload.categories;
    },
    SAVE_ORIGINAL_ARRAY_ONCE(state, payload) {
      const categoriesFromJSON = createCategories(payload);
      state.categories = categoriesFromJSON;
    },
  },

  getters: {
    categoryState: (state) => state.categories,
  },

  actions: {
    setDevEmpty({ commit }, payload) {
      commit('DEV_EMPTY', payload);
    },
    setReplace({ commit }, payload) {
      commit('REPLACE', payload);
    },
    setFromMock({ commit }, payload) {
      commit('STANDARD', payload);
    },
    storeOriginalArray({ commit }, payload) {
      commit('SAVE_ORIGINAL_ARRAY_ONCE', payload);
    },
  },
};

export default categories;
