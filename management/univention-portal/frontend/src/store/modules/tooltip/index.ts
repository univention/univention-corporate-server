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
import { Commit } from 'vuex';
import { PortalModule } from '../../root.models';
import { Tooltip } from './tooltip.models';

export interface TooltipState {
  tooltip: Tooltip | null,
  hoverOnToolip: boolean,
  tooltipID: number | null,
}

const tooltip: PortalModule<TooltipState> = {
  namespaced: true,
  state: { tooltip: null, hoverOnToolip: false, tooltipID: null },

  mutations: {
    SETTOOLTIP: (state: TooltipState, payload: TooltipState): void => {
      state.tooltip = payload.tooltip;
    },
    SET_HOVER_ON_TOOLIP: (state: TooltipState, payload: boolean): void => {
      state.hoverOnToolip = payload;
    },
    SET_TOOLTIP_ID: (state: TooltipState, payload: number): void => {
      state.tooltipID = payload;
    },
  },

  getters: {
    tooltip: (state) => state.tooltip,
    tooltipIsHovered: (state) => state.hoverOnToolip,
    getTooltipID: (state) => state.tooltipID,
  },

  actions: {
    setTooltip({ commit }: { commit: Commit }, payload: TooltipState): void {
      commit('SETTOOLTIP', payload);
    },
    unsetTooltip({ commit }: { commit: Commit }): void {
      commit('SETTOOLTIP', { tooltip: null });
    },
    setHoverOnTooltip({ commit }: { commit: Commit }, payload: boolean): void {
      commit('SET_HOVER_ON_TOOLIP', payload);
    },
    setTooltipID({ commit }: { commit: Commit }, payload: number): void {
      commit('SET_TOOLTIP_ID', payload);
    },
  },
};

export default tooltip;
