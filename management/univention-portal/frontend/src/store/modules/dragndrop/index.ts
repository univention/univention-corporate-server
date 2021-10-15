/*
 * Copyright 2021 Univention GmbH
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
import { ActionContext } from 'vuex';

export interface DraggedItem {
  dn: string,
  superDn: string,
  originalContent: string[][],
}

export interface DraggedItemDragCopy {
  dn: string,
  superDn: string,
  original: boolean,
  originalContent: string[][],
}

type DragAndDropActionContext = ActionContext<DraggedItem, RootState>;

const dragndrop: PortalModule<DraggedItem> = {
  namespaced: true,
  state: {
    dn: '',
    superDn: '',
    originalContent: [],
  },

  mutations: {
    SET_IDS(state: DraggedItem, payload: DraggedItemDragCopy): void {
      state.dn = payload.dn;
      state.superDn = payload.superDn;
      if (payload.originalContent) {
        state.originalContent = payload.originalContent;
      }
    },
  },

  getters: {
    getId: (state) => state,
    inDragnDropMode: (state) => !!state.dn,
  },

  actions: {
    startDragging({ commit, rootGetters }: DragAndDropActionContext, payload: DraggedItemDragCopy): void {
      let content = null;
      if (payload.original) {
        content = rootGetters['portalData/portalContent'];
      }
      commit('SET_IDS', {
        dn: payload.dn,
        superDn: payload.superDn,
        originalContent: content,
      });
    },
    dropped({ commit }: DragAndDropActionContext): void {
      commit('SET_IDS', {
        dn: '',
        superDn: '',
        originalContent: [],
      });
    },
    revert({ dispatch, getters }: DragAndDropActionContext): void {
      const content = getters.getId.originalContent;
      if (content.length) {
        dispatch('portalData/replaceContent', content, { root: true });
      }
    },
  },
};

export default dragndrop;
