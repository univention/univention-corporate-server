import { PortalModule } from '../types';

export interface NavigationState {
  activeButton: string;
}

const navigation: PortalModule<NavigationState> = {
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
