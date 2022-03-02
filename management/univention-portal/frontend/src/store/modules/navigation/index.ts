/*
 * Copyright 2021-2022 Univention GmbH
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
    setActiveButton({ commit, dispatch } : { commit: Commit, dispatch: Dispatch }, id: NavigationButton): void {
      dispatch('modal/hideAndClearModal', undefined, { root: true });
      if (id === 'search') {
        dispatch('tabs/setActiveTab', 0, { root: true });
      }
      if (id === 'bell') {
        dispatch('notifications/hideAllNotifications', undefined, { root: true });
      }
      if (id) {
        dispatch('activity/setLevel', `header-${id}`, { root: true });
      } else {
        dispatch('activity/setLevel', 'portal', { root: true });
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
