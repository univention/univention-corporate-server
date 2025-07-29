/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { Commit, Dispatch } from 'vuex';
import { PortalModule } from '../../root.models';
import { NavigationButton } from './navigation.models';

export interface NavigationState {
  activeButton: NavigationButton;
}

const navigation: PortalModule<NavigationState> = {
  namespaced: true,
  state: { activeButton: '' },

  mutations: {
    ACTIVEBUTTON(state: NavigationState, id: NavigationButton): void {
      state.activeButton = id;
    },
  },

  getters: { getActiveButton: (state) => state.activeButton },

  actions: {
    setActiveButton({ commit, dispatch, rootGetters } : { commit: Commit, dispatch: Dispatch, rootGetters: any }, id: NavigationButton): void {
      let folderIsOpen = rootGetters['modal/inFolderModal'];
      const willBeSearchAndFolderIsOpen = id === 'search' && folderIsOpen;
      const wasSearchAndFolderIsOpen = !id && folderIsOpen;
      if (!(willBeSearchAndFolderIsOpen || wasSearchAndFolderIsOpen)) {
        dispatch('modal/hideAndClearModal', undefined, { root: true });
        folderIsOpen = false;
      }
      if (id === 'search') {
        dispatch('tabs/setActiveTab', 0, { root: true });
      }
      if (id === 'bell') {
        dispatch('notifications/hideAllNotifications', undefined, { root: true });
      }
      if (!folderIsOpen) {
        if (id) {
          dispatch('activity/setLevel', `header-${id}`, { root: true });
        } else {
          dispatch('activity/setLevel', 'portal', { root: true });
        }
      }
      commit('ACTIVEBUTTON', id);
    },
    closeNotificationsSidebar({ dispatch, getters }: { dispatch: Dispatch, getters: any }): void {
      if (getters.getActiveButton === 'bell') {
        dispatch('setActiveButton', '');
        dispatch('activity/setRegion', 'portal-header', { root: true });
      }
    },
  },
};

export default navigation;
