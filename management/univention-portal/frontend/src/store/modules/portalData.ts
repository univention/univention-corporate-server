import { PortalData } from '../models';
import { PortalModule } from '../types';

export interface PortalDataState {
  portal: PortalData;
  editMode: boolean;
}

const portalData: PortalModule<PortalDataState> = {
  namespaced: true,
  state: {
    portal: {
      portal: {
        name: {
          en_US: 'Univention Portal',
        },
        background: null,
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

export default portalData;
