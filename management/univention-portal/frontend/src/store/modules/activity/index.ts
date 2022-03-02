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
import { ActionContext } from 'vuex';

import { PortalModule, RootState } from '../../root.models';

interface Message {
  id: string,
  msg: string,
}

export interface Activity {
  level: string,
  focus: Record<string, string>,
  region: string | null,
  messages: Record<string, Message>,
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
    region: 'portal-header',
    messages: {},
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
    ADD_MESSAGE(state: Activity, message: Message): void {
      state.messages[message.id] = message;
    },
    REMOVE_MESSAGE(state: Activity, id: string): void {
      delete state.messages[id];
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
    announce: (state: Activity) => Object.values(state.messages),
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
    addMessage({ commit }: ActivityActionContext, message: Message): void {
      commit('ADD_MESSAGE', message);
    },
    removeMessage({ commit }: ActivityActionContext, id: string): void {
      commit('REMOVE_MESSAGE', id);
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
