import { Module } from 'vuex';

export interface Portal {
  name: Record<string, string>;
}

export interface PortalData {
  portal: Portal;
}

export interface State {
  portal: PortalData;
  editMode: boolean;
}

const portal: Module<State, unknown> = {
  namespaced: true,
  state: {
    portal: {
      portal: {
        name: {
          en_US: 'Univention Portal',
        },
      },
    },
    editMode: false,
  },

  mutations: {
    PORTALDATA(state, payload) {
      state.portal = payload;
    },
    EDITMODE(state, editMode) {
      state.editMode = editMode;
    },
  },

  getters: {
    getPortal: (state) => state.portal,
    portalName: (state) => state.portal.portal.name,
    editMode: (state) => state.editMode,
  },

  actions: {
    setPortal({ commit }, payload) {
      commit('PORTALDATA', payload);
    },
    setEditMode({ commit }, editMode) {
      commit('EDITMODE', editMode);
    },
  },
};

export default portal;
