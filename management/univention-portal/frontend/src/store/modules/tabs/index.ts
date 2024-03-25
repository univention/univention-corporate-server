/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2021-2024 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
import { Dispatch, Commit } from 'vuex';
import { PortalModule } from '@/store/root.models';
import { Tab } from './tabs.models';

export interface TabState {
  activeTabId: number;
  tabs: Tab[];
  scrollPosition: number;
}

let nextId = 1; // 0 is reserved for portal overview
const tabs: PortalModule<TabState> = {
  namespaced: true,
  state: {
    activeTabId: 0,
    tabs: [],
    scrollPosition: 0,
  },

  mutations: {
    ACTIVE_TAB(state: TabState, id: number): void {
      state.activeTabId = id;
    },
    ADD_TAB(state: TabState, tab: Tab): void {
      let alreadyExistingTabIndex = -1;
      if (tab.target) {
        alreadyExistingTabIndex = state.tabs.findIndex((stateTab) => stateTab.target === tab.target);
      } else {
        alreadyExistingTabIndex = state.tabs.findIndex((stateTab) => stateTab.tabLabel === tab.tabLabel);
      }
      if (alreadyExistingTabIndex === -1) {
        tab.id = nextId;
        nextId += 1;
        state.tabs.push(tab);
        state.activeTabId = tab.id;
      } else {
        tab.id = state.tabs[alreadyExistingTabIndex].id;
        state.tabs[alreadyExistingTabIndex] = tab;
        state.activeTabId = tab.id;
      }
    },
    DELETE_TAB(state: TabState, id: number): void {
      const tabIndex = state.tabs.findIndex((stateTab) => stateTab.id === id);
      if (tabIndex !== -1) {
        state.tabs.splice(tabIndex, 1);
      }
      if (state.activeTabId === id) {
        state.activeTabId = 0;
      }
    },
    SAVE_SCROLL_POSITION(state: TabState): void {
      if (state.activeTabId === 0) {
        state.scrollPosition = window.scrollY;
      }
    },
  },

  getters: {
    allTabs: (state) => state.tabs,
    numTabs: (state) => state.tabs.length,
    activeTabId: (state) => state.activeTabId,
    savedScrollPosition: (state) => state.scrollPosition,
  },

  actions: {
    setActiveTab({ getters, commit, dispatch }: { getters: any, commit: Commit, dispatch: Dispatch }, id: number): void {
      if (getters.activeTabId === id) {
        return;
      }
      dispatch('navigation/setActiveButton', '', { root: true });
      dispatch('modal/hideAndClearModal', undefined, { root: true });
      commit('SAVE_SCROLL_POSITION');
      commit('ACTIVE_TAB', id);
    },
    addTab({ commit }: { commit: Commit }, tab: Tab): void {
      commit('SAVE_SCROLL_POSITION');
      commit('ADD_TAB', tab);
    },
    deleteTab({ commit }: { commit: Commit}, id: number): void {
      commit('DELETE_TAB', id);
    },
  },
};

export default tabs;
