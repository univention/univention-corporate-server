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
import { PortalModule, RootState } from '@/store/root.models';
import { ActionContext, Commit, Dispatch } from 'vuex';
import { ModalComponentInterface, ModalProp, ModalLevel } from './modal.models';

export interface ModalState {
  firstLevelModal: {
    modalVisible: boolean;
    modalComponent: string | null;
    modalProps:ModalProp;
    modalStubborn: boolean;
    modalResolve: (any) => void;
    modalReject: () => void;
  }
  // secondLevel Modals are mostly used for confirmation dialogs, another layer of option form.
  // A11Y: When creating a second Modal you should set also the activity layer.
  secondLevelModal: {
    modalVisible: boolean;
    modalComponent: string | null;
    modalProps: ModalProp;
    modalStubborn: boolean;
    modalResolve: (any) => void;
    modalReject: () => void;
  }
}

type ModalActionContext = ActionContext<ModalState, RootState>;

const modal: PortalModule<ModalState> = {
  namespaced: true,
  state: {
    firstLevelModal: {
      modalVisible: false,
      modalComponent: null,
      modalProps: {},
      modalStubborn: false,
      modalResolve: (() => undefined),
      modalReject: (() => undefined),
    },
    secondLevelModal: {
      modalVisible: false,
      modalComponent: null,
      modalProps: {},
      modalStubborn: false,
      modalResolve: (() => undefined),
      modalReject: (() => undefined),
    },
  },

  mutations: {
    CHANGE_MODAL_PROPS(state: ModalState, payload: ModalProp): void {
      // console.log('CHANGE_MODAL_PROPS', payload);
      const modalLevel = payload.level === 2 ? 'secondLevelModal' : 'firstLevelModal';
      // console.log('modalLevel', payload.level);
      // console.log('BEFORE', state[modalLevel].modalProps);
      state[modalLevel].modalProps = { ...state[modalLevel].modalProps, ...payload.props };
      // console.log('AFTER', state[modalLevel].modalProps);
    },
    SET_MODAL(state: ModalState, payload: ModalComponentInterface): void {
      const modalLevel = payload.level === 2 ? 'secondLevelModal' : 'firstLevelModal';
      state[modalLevel].modalComponent = payload.name;
      state[modalLevel].modalProps = payload.props || {};
      state[modalLevel].modalStubborn = payload.stubborn || false;
      state[modalLevel].modalResolve = payload.resolve || (() => undefined);
      state[modalLevel].modalReject = payload.reject || (() => undefined);
    },
    CLEAR_MODAL(state: ModalState, payload: ModalLevel): void {
      const modalLevel = payload === 2 ? 'secondLevelModal' : 'firstLevelModal';
      state[modalLevel].modalComponent = null;
      state[modalLevel].modalProps = {};
      state[modalLevel].modalStubborn = false;
      state[modalLevel].modalResolve = () => undefined;
      state[modalLevel].modalReject = () => undefined;
    },
    SHOW_MODAL(state: ModalState, payload: ModalLevel): void {
      const modalLevel = payload === 2 ? 'secondLevelModal' : 'firstLevelModal';
      state[modalLevel].modalVisible = true;
    },
    HIDE_MODAL(state: ModalState, payload: ModalLevel): void {
      const modalLevel = payload === 2 ? 'secondLevelModal' : 'firstLevelModal';
      state[modalLevel].modalVisible = false;
    },
    RESOLVE(state: ModalState, payload): void {
      const modalLevel = payload.level === 2 ? 'secondLevelModal' : 'firstLevelModal';
      state[modalLevel].modalResolve(payload);
    },
    REJECT(state: ModalState, payload): void {
      const modalLevel = payload === 2 ? 'secondLevelModal' : 'firstLevelModal';
      state[modalLevel].modalReject();
    },
    ENABLE_BODY_SCROLLING(): void {
      document.body.classList.remove('body--has-modal');
    },
    DISABLE_BODY_SCROLLING(): void {
      document.body.classList.add('body--has-modal');
    },
  },

  getters: {
    inFolderModal: (state) => state.firstLevelModal.modalComponent === 'PortalFolder',
    getModalState: (state) => (level: string) => state[level].modalVisible,
    getModalComponent: (state) => (level: string) => state[level].modalComponent,
    getModalProps: (state) => (level: string) => state[level].modalProps,
    getModalStubborn: (state) => (level: string) => state[level].modalStubborn,
  },

  actions: {
    changeModalProps({ commit }: { commit: Commit }, payload: Array<string>): void {
      commit('CHANGE_MODAL_PROPS', payload);
    },
    setAndShowModal({ commit, dispatch }: ModalActionContext, payload: ModalComponentInterface): void {
      commit('SET_MODAL', payload);
      commit('SHOW_MODAL', payload.level);
      commit('DISABLE_BODY_SCROLLING');
      const activityLevel = payload.level === 2 ? 'modal2' : 'modal';
      dispatch('activity/setLevel', activityLevel, { root: true });
    },
    setShowModalPromise({ dispatch }: { dispatch: Dispatch}, payload: ModalComponentInterface): Promise<void> {
      return new Promise((resolve, reject) => {
        dispatch('setAndShowModal', { ...payload, resolve, reject });
      });
    },
    hideAndClearModal({ getters, commit, dispatch }: ModalActionContext, payload?: ModalLevel): void {
      if (getters.getModalState) {
        const activityLevel = payload === 2 ? 'modal' : 'portal';
        dispatch('activity/setLevel', activityLevel, { root: true });
      }
      commit('HIDE_MODAL', payload);
      commit('CLEAR_MODAL', payload);
      if (payload !== 2) {
        commit('ENABLE_BODY_SCROLLING');
      }
    },
    resolve({ state, commit }, payload: ModalComponentInterface): void {
      commit('RESOLVE', payload);
    },
    reject({ state, commit }, payload?: ModalLevel): void {
      commit('REJECT', payload);
    },
    enableBodyScrolling({ commit }: { commit: Commit}): void {
      commit('ENABLE_BODY_SCROLLING');
    },
    disableBodyScrolling({ commit }: { commit: Commit}): void {
      commit('DISABLE_BODY_SCROLLING');
    },
    closeFolder({ getters, dispatch }: ModalActionContext): void {
      if (getters.inFolderModal) {
        dispatch('modal/hideAndClearModal', null, { root: true });
        dispatch('tooltip/unsetTooltip', null, { root: true });
        dispatch('activity/setRegion', 'portalCategories', { root: true });
      }
    },
  },
};

export default modal;
