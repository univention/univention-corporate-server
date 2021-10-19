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
import { PortalBaseLayout } from '@/store/modules/portalData/portalData.models';

export interface DraggedItem {
  layoutId: string,
  draggedType: string,
  originalLayout: null | PortalBaseLayout,
}

export interface DraggedItemDragCopy {
  layoutId: string,
  draggedType: undefined | string,
  saveOriginalLayout: undefined | boolean,
  originalLayout: undefined | null | PortalBaseLayout,
}

type DragAndDropActionContext = ActionContext<DraggedItem, RootState>;

const dragndrop: PortalModule<DraggedItem> = {
  namespaced: true,
  state: {
    layoutId: '',
    draggedType: '',
    originalLayout: null,
  },

  mutations: {
    SET_IDS(state: DraggedItem, payload: DraggedItem): void {
      state.layoutId = payload.layoutId;
      if (payload.draggedType !== undefined) {
        state.draggedType = payload.draggedType;
      }
      if (payload.originalLayout !== undefined) {
        state.originalLayout = payload.originalLayout;
      }
    },
  },

  getters: {
    getId: (state) => state,
    inDragnDropMode: (state) => !!state.layoutId,
  },

  actions: {
    startDragging({ commit, rootGetters }: DragAndDropActionContext, payload: DraggedItemDragCopy): void {
      let layout;
      if (payload.saveOriginalLayout) {
        layout = JSON.parse(JSON.stringify(rootGetters['portalData/portalLayout']));
      }
      commit('SET_IDS', {
        layoutId: payload.layoutId,
        draggedType: payload.draggedType,
        originalLayout: layout,
      });
    },
    dropped({ commit }: DragAndDropActionContext): void {
      commit('SET_IDS', {
        layoutId: '',
        draggedType: '',
        originalLayout: null,
      });
    },
    cancelDragging({ dispatch, getters }: DragAndDropActionContext): void {
      const layout = getters.getId.originalLayout;
      if (layout) {
        dispatch('portalData/setLayout', layout, { root: true });
      }
      dispatch('dropped');
    },
  },
};

export default dragndrop;
