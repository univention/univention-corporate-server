// plugins/localize
import { Locale } from '@/store/models';
import { App } from 'vue';
import { store } from '../store';

// import { store } from '@/store';

export type Localized = (input: Record<Locale, string>) => string;

// expects an object, returns a string
const localize = {
  install: (app: App): void => {
    const localized: Localized = (input: Record<Locale, string>) => {
      const curLocale = store.getters['locale/getLocale'];
      const shortLocale = curLocale.split('_')[0];
      return input[curLocale] || input[shortLocale] || input.en || input.en_US;
    };
    app.config.globalProperties.$localized = localized;
  },
};

declare module '@vue/runtime-core' {
  // Bind to `this` keyword
  interface ComponentCustomProperties {
    $localized: Localized;
  }
}

// Usage example:
// {{ $localized(label) }}
export default localize;
