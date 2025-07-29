/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { Module, ActionContext } from 'vuex';

/* eslint-disable-next-line @typescript-eslint/no-empty-interface */
export interface RootState {
  loadingState: boolean,
  initialLoadDone: boolean,
}

export type PortalModule<S> = Module<S, RootState>;
export type PortalActionContext<S> = ActionContext<S, RootState>;

export const initialRootState: RootState = {
  loadingState: true,
  initialLoadDone: false,
};
