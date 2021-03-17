import { Tab } from '../models';
import { PortalModule } from '../types';

export interface TabState {
  activeTabIndex: number;
  tabs: Tab[];
}

const tabs: PortalModule<TabState> = {
  namespaced: true,
  state: {
    activeTabIndex: 0,
    tabs: [],
  },

  mutations: {
    ALL_TABS(state, payload: Tab[]) {
      state.tabs = payload;
    },
    ACTIVE_TAB(state, index: number) {
      state.activeTabIndex = index;
    },
    ADD_TAB(state, tab: Tab) {
      const index = state.tabs.findIndex((stateTab) => stateTab.tabLabel === tab.tabLabel);
      if (index === -1) {
        state.tabs.push(tab);
        state.activeTabIndex = state.tabs.length;
      } else {
        state.activeTabIndex = index + 1;
      }
    },
    DELETE_TAB(state, index: number) {
      state.tabs.splice(index - 1, 1);
      state.activeTabIndex = 0;
    },
  },

  getters: {
    allTabs: (state) => state.tabs,
    activeTabIndex: (state) => state.activeTabIndex,
  },

  actions: {
    setAllTabs({ commit }, payload: Array<Tab>) {
      commit('ALL_TABS', payload);
    },
    setActiveTab({ commit }, index: number) {
      commit('ACTIVE_TAB', index);
    },
    addTab({ commit }, tab: Tab) {
      commit('ADD_TAB', tab);
    },
    deleteTab({ commit }, index: number) {
      commit('DELETE_TAB', index);
    },
  },
};

export default tabs;
