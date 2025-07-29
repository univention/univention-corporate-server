/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
// plugins/localize
import { Locale } from '@/store/modules/locale/locale.models';
import { App } from 'vue';
import { store } from '@/store';

type Localized = (input: Record<Locale, string>) => string;

// expects an object, returns a string
export function localized(input: Record<Locale, string>): string {
  const curLocale = store.getters['locale/getLocale'];
  const shortLocale = curLocale.split('_')[0];
  let ret = '';

  if (input) {
    ret = input[curLocale] || input[shortLocale] || input.en || input.en_US || '';
  }
  return ret;
}

declare module '@vue/runtime-core' {
  // Bind to `this` keyword
  interface ComponentCustomProperties {
    $localized: Localized;
  }
}

// Usage example:
// {{ $localized(label) }}
export default {
  install: (app: App): void => {
    app.config.globalProperties.$localized = localized;
  },
};
