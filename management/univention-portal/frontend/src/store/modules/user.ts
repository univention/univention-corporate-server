import { User } from '../models';
import { PortalModule } from '../types';

export interface UserState {
  user: User;
}

const user: PortalModule<UserState> = {
  namespaced: true,
  state: {
    user: {
      username: '',
      displayName: '',
      mayEditPortal: false,
      mayLoginViaSAML: false,
    },
  },

  mutations: {
    SETUSER: (state, payload) => {
      state.user = payload.user;
    },
  },

  getters: {
    userState: (state) => state.user,
  },

  actions: {
    setUser({ commit }, payload) {
      commit('SETUSER', payload);
    },
  },
};

export default user;
