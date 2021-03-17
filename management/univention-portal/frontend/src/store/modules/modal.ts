import { PortalModule } from '../types';

export interface ModalState {
  modalVisible: boolean;
  modalComponent: unknown;
  modalProps: unknown;
  modalStubborn: boolean;
}

const modal: PortalModule<ModalState> = {
  namespaced: true,
  state: {
    modalVisible: false,
    modalComponent: null,
    modalProps: {},
    modalStubborn: false,
  },

  mutations: {
    SHOWMODAL(state, payload) {
      state.modalVisible = true;
      state.modalComponent = payload.name;
      state.modalProps = payload.props || {};
      state.modalStubborn = payload.stubborn || false;
    },
    HIDEMODAL(state) {
      state.modalVisible = false;
      state.modalComponent = null;
      state.modalProps = {};
      state.modalStubborn = false;
    },
  },

  getters: {
    modalState: (state) => state.modalVisible,
    modalComponent: (state) => state.modalComponent,
    modalProps: (state) => state.modalProps,
    modalStubborn: (state) => state.modalStubborn,
  },

  actions: {
    setShowLoadingModal({ commit }) {
      commit('SHOWMODAL', { name: 'PortalStandby' });
    },
    setShowModal({ commit }, payload) {
      commit('SHOWMODAL', payload);
    },
    setHideModal({ commit }) {
      commit('HIDEMODAL');
    },
  },
};

export default modal;
