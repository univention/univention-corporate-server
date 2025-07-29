/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { PortalModule, RootState } from '@/store/root.models';
import { ActionContext } from 'vuex';
import { PortalBaseLayout, PortalLayout } from '@/store/modules/portalData/portalData.models';

export interface DraggedItem {
  layoutId: string,
  draggedType: string,
  dragType: 'mouse' | 'keyboard',
  originalLayout: null | {layout: PortalLayout, baseLayout: PortalBaseLayout},
  lastDir: 'left' | 'right' | 'up' | 'down',
  isWindowMouseListenerSet: boolean,
  title: string,
}
export type DragType = 'mouse' | 'keyboard';
export interface DraggedItemDragCopy {
  layoutId: string,
  draggedType: undefined | string,
  dragType: 'mouse' | 'keyboard',
  saveOriginalLayout: undefined | boolean,
  originalLayout: undefined | null | {layout: PortalLayout, baseLayout: PortalBaseLayout},
  lastDir: 'left' | 'right' | 'up' | 'down',
}

type DragAndDropActionContext = ActionContext<DraggedItem, RootState>;

const dragndrop: PortalModule<DraggedItem> = {
  namespaced: true,
  state: {
    layoutId: '',
    draggedType: '',
    dragType: 'mouse',
    originalLayout: null,
    lastDir: 'left',
    isWindowMouseListenerSet: false,
    title: '',
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
      state.dragType = payload.dragType || 'mouse';
    },
    LAST_DIR(state, payload): void {
      state.lastDir = payload;
    },
    IS_WINDOW_MOUSE_LISTENER_SET(state, payload): void {
      state.isWindowMouseListenerSet = payload;
    },
  },

  getters: {
    getId: (state) => state,
    inDragnDropMode: (state) => !!state.layoutId,
    inKeyboardDragnDropMode: (state, getters) => getters.inDragnDropMode && state.dragType === 'keyboard',
    getLastDir: (state) => state.lastDir,
    isWindowMouseListenerSet: (state) => state.isWindowMouseListenerSet,
  },

  actions: {
    startDragging({ commit, dispatch, getters, rootGetters }: DragAndDropActionContext, payload: DraggedItemDragCopy): void {
      let layout;
      if (payload.saveOriginalLayout) {
        layout = {
          layout: JSON.parse(JSON.stringify(rootGetters['portalData/portalLayout'])),
          baseLayout: JSON.parse(JSON.stringify(rootGetters['portalData/portalBaseLayout'])),
        };
      }
      commit('SET_IDS', {
        layoutId: payload.layoutId,
        draggedType: payload.draggedType,
        originalLayout: layout,
        dragType: payload.dragType,
      });
      dispatch('activity/saveFocus', {
        region: 'portalCategories',
        id: `${payload.layoutId}-move-button`,
      }, { root: true });
      if (payload.dragType === 'keyboard' && !getters.isWindowMouseListenerSet) {
        window.addEventListener('mousedown', (evt) => {
          dispatch('maybeCancelDragging');
          commit('IS_WINDOW_MOUSE_LISTENER_SET', false);
        }, { once: true, capture: true });
        commit('IS_WINDOW_MOUSE_LISTENER_SET', true);
      }
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
      dispatch('activity/focusElement', 'portalCategories', { root: true });
    },
    maybeCancelDragging({ dispatch, getters }: DragAndDropActionContext): void {
      if (getters.inKeyboardDragnDropMode) {
        dispatch('cancelDragging');
      }
    },
    lastDir({ commit }: DragAndDropActionContext, payload): void {
      commit('LAST_DIR', payload);
    },
  },
};

export default dragndrop;
