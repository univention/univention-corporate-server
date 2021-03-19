import createMenuStructure from '@/jsHelper/createMenuStructure';
import addLanguageTile from '@/jsHelper/addLanguageTile';
import { PortalModule } from '../types';

export interface MenuState {
  menu: Record<string, unknown>;
  menuLinks: Array<unknown>,
  userLinks: Array<unknown>,
}

const menu: PortalModule<MenuState> = {
  namespaced: true,
  state: {
    menu: {},
    menuLinks: [],
    userLinks: [],
  },

  mutations: {
    MENU(state, payload) {
      const menuStructure = createMenuStructure(payload.portal);
      const languageMenuLink = addLanguageTile(payload.availableLocales);
      menuStructure.unshift(languageMenuLink);
      state.menu = menuStructure;
    },
    MENU_LINKS(state, payload) {
      state.menuLinks = payload;
    },
    USER_LINKS(state, payload) {
      state.userLinks = payload;
    },
  },

  getters: {
    getMenu: (state) => state.menu,
    getMenuLinks: (state) => state.menuLinks,
    getUserLinks: (state) => state.userLinks,
  },

  actions: {
    setMenu({ commit }, payload) {
      commit('MENU', payload);
    },
    setMenuLinks({ commit }, payload) {
      commit('MENU_LINKS', payload);
    },
    setUserLinks({ commit }, payload) {
      commit('USER_LINKS', payload);
    },
  },
};

export default menu;
