/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { store } from '@/store/';

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $store: store;
  }
}
