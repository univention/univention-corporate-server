/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { ActionContext } from 'vuex';

import { PortalModule, RootState } from '../../root.models';

export interface Activity {
  level: string,
  focus: Record<string, string>,
  region: string | null,
  message: string,
}

type ActivityActionContext = ActionContext<Activity, RootState>;

interface SaveFocusArgs {
  region?: string,
  id: string,
}

const activity: PortalModule<Activity> = {
  namespaced: true,
  state: {
    level: 'portal',
    focus: {},
    region: '',
    message: '',
  },

  mutations: {
    ADD_REGION(state: Activity, region: string): void {
      state.focus[region] = state.focus[region] || '';
    },
    SET_REGION(state: Activity, region: string | null): void {
      state.region = region;
    },
    SET_LEVEL(state: Activity, level: string): void {
      state.level = level;
    },
    SET_MESSAGE(state: Activity, message: string): void {
      state.message = message;
    },
    SAVE_FOCUS(state: Activity, payload: SaveFocusArgs): void {
      let region = payload.region;
      const targetElem = document.getElementById(payload.id);
      if (!region && state.region) {
        const regionElem = document.getElementById(state.region);
        if (regionElem) {
          if (regionElem.contains(targetElem)) {
            region = state.region;
          }
        }
      }
      if (!region) {
        let foundRegion: HTMLElement | null = null;
        Object.entries(state.focus).forEach(([focusRegion]) => {
          const regionElem = document.getElementById(focusRegion);
          if (regionElem) {
            if (foundRegion && regionElem.contains(foundRegion)) {
              return;
            }
            if (regionElem.contains(targetElem)) {
              region = focusRegion;
              foundRegion = regionElem;
            }
          }
        });
      }
      if (region) {
        state.focus[region] = payload.id;
      }
    },
  },

  getters: {
    level: (state: Activity) => state.level,
    focus: (state: Activity) => state.focus,
    region: (state: Activity) => state.region,
    message: (state: Activity) => state.message,
  },

  actions: {
    addRegion({ commit }: ActivityActionContext, region: string): void {
      commit('ADD_REGION', region);
    },
    setRegion({ dispatch, commit }: ActivityActionContext, region: string | null): void {
      commit('SET_REGION', region);
      dispatch('focusElement', region);
    },
    setLevel({ commit }: ActivityActionContext, level: string): void {
      commit('SET_LEVEL', level);
    },
    setMessage({ commit }: ActivityActionContext, message: string): void {
      commit('SET_MESSAGE', message);
    },
    async focusElement({ getters }: ActivityActionContext, region: string | null): Promise<void> {
      if (!region) {
        return;
      }
      setTimeout(() => {
        const id = getters.focus[region];
        let elem = document.getElementById(id);
        if (!elem) {
          const regionElem = document.getElementById(region);
          const activeElem = regionElem?.querySelector('[tabindex="0"][id]');
          if (activeElem) {
            elem = document.getElementById(activeElem.id);
          }
        }
        elem?.focus();
      }, 50);
    },
    saveFocus({ commit }: ActivityActionContext, payload: SaveFocusArgs): void {
      if (payload.id) {
        commit('SAVE_FOCUS', payload);
      }
    },
  },
};

export default activity;
