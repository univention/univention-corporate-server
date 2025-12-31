/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { Commit } from 'vuex';
import addLanguageTile from '@/jsHelper/addLanguageTile';
import createMenuStructure from '@/jsHelper/createMenuStructure';
import createUserMenu from '@/jsHelper/createUserMenu';
import { PortalModule } from '@/store/root.models';

export interface MenuState {
  menu: Array<unknown>;
  disabled: Array<string>;
}

const menu: PortalModule<MenuState> = {
  namespaced: true,
  state: {
    menu: [],
    disabled: [],
  },

  mutations: {
    MENU(state : MenuState, payload: Record<string, unknown>): void {
      const menuStructure = createMenuStructure(payload.portal);
      const languageMenuLink = addLanguageTile(payload.availableLocales);
      const userLinks = createUserMenu(payload.portal);
      if (languageMenuLink) {
        menuStructure.unshift(languageMenuLink);
      }
      if (userLinks) {
        menuStructure.unshift(userLinks);
      }
      state.menu = menuStructure;
    },
    DISABLED(state : MenuState, payload: string[]): void {
      state.disabled = payload;
    },
  },

  getters: {
    getMenu: (state : MenuState) => state.menu,
    disabledMenuItems: (state : MenuState) => state.disabled,
  },

  actions: {
    setMenu({ commit }: { commit: Commit}, payload: Record<string, unknown>): void {
      commit('MENU', payload);
    },
    setDisabled({ commit } : { commit: Commit}, payload: Record<string, unknown>): void {
      commit('DISABLED', payload);
    },
  },
};

export default menu;
