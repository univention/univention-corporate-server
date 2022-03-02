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
import { ActionContext } from 'vuex';
import _ from '@/jsHelper/translate';
import { PortalModule, RootState } from '../../root.models';
import { User, UserWrapper } from './user.models';

export interface UserState {
  user: User;
}

type UserActionContext = ActionContext<UserState, RootState>;

const user: PortalModule<UserState> = {
  namespaced: true,
  state: {
    user: {
      username: '',
      displayName: '',
      mayEditPortal: false,
      authMode: 'ucs',
    },
  },

  mutations: {
    SETUSER: (state: UserState, payload: UserWrapper): void => {
      state.user = payload.user;
    },
  },

  getters: { userState: (state) => state.user },

  actions: {
    setUser({ commit, dispatch }: UserActionContext, payload: UserWrapper): void {
      commit('SETUSER', payload);
      const username = payload.user.username;
      if (username) {
        dispatch('activity/addMessage', {
          id: 'login',
          msg: _('Logged in as "%(username)s"', { username }),
        }, { root: true });
      } else {
        dispatch('activity/addMessage', {
          id: 'login',
          msg: _('Not logged in'),
        }, { root: true });
      }
    },
  },
};

export default user;
