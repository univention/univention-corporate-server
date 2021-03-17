import createCategories from '@/jsHelper/createCategories';
import { Category } from '../models';
import { PortalModule } from '../types';

export interface CategoryState {
  categories: Category[];
}

const categories: PortalModule<CategoryState> = {
  namespaced: true,
  state: {
    categories: [],
  },
  mutations: {
    SET_EMPTY(state) {
      state.categories = [];
    },
    SET_REPLACE(state, payload: Category[]) {
      state.categories = payload;
    },
  },
  getters: {
    getCategories: (state) => state.categories,
  },
  actions: {
    setEmpty({ commit }) {
      commit('SET_EMPTY');
    },
    setReplace({ commit }, payload: Category[]) {
      commit('SET_REPLACE', payload);
    },
    setOriginalArray({ commit }, payload) {
      const categoriesFromJSON: Category[] = createCategories(payload);
      commit('SET_REPLACE', categoriesFromJSON);
    },
  },
};

export default categories;
