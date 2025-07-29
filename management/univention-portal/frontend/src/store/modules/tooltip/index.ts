/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
