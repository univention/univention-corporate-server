/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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

  getters: {
    userState: (state: UserState) => state.user,
  },

  actions: {
    setUser({ commit, dispatch }: UserActionContext, payload: UserWrapper): void {
      commit('SETUSER', payload);
      const username = payload.user.username;
      if (username) {
        dispatch('activity/setMessage', _('Logged in as "%(username)s"', { username }), { root: true });
      } else {
        dispatch('activity/setMessage', _('Not logged in'), { root: true });
      }
    },
  },
};

export default user;
