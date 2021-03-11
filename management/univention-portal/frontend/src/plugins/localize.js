// plugins/localize.js
import { store } from '@/store';

// expects an object, returns a string
const localize = {
  install: (app) => {
    // eslint-disable-next-line no-param-reassign
    app.config.globalProperties.$localized = (label) => {
      const curLocale = store.state.locale.locale;
      return label[curLocale] || label.en || label.en_US;
    };
  },
};

// Usage example:
// {{ $localized(label) }}
export default localize;
