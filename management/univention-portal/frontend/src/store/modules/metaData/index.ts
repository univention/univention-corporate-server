/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { PortalModule } from '@/store/root.models';
import { Commit } from 'vuex';

export interface MetaDataState {
  meta: Record<string, unknown>;
}

const metaData: PortalModule<MetaDataState> = {
  namespaced: true,
  state: {
    meta: {
      cookieBanner: {
        show: false,
        title: { en: '' },
        text: { en: '' },
        domains: [],
      },
    },
  },

  mutations: {
    META(state: MetaDataState, payload: Record<string, unknown>): void {
      state.meta = payload;
    },
  },

  getters: { getMeta: (state) => state.meta },

  actions: {
    setMeta({ commit }: { commit: Commit }, payload: Record<string, unknown>): void {
      commit('META', payload);
    },
  },
};

export default metaData;
