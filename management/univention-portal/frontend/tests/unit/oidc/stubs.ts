/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import vuex from 'vuex';

import notifications from '@/store/modules/notifications';
import oidc from '@/store/modules/oidc';

export const createStubStore = () => new vuex.Store<any>({
  modules: {
    notifications,
    oidc,
  },
});

export default createStubStore;
