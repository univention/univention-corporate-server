/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { createApp } from 'vue';
import App from '@/App.vue';
import { store } from '@/store';
import { router } from '@/router';
import localize from '@/plugins/localize';
import VueDOMPurifyHTML from 'vue-dompurify-html';

import '@/assets/styles/style.styl';
import addCustomStyles from '@/jsHelper/addCustomStyles';

addCustomStyles();

declare global {
    interface Window {
        store: any;
    }
}
window.store = store;

const app = createApp(App)
  .use(localize)
  .use(router)
  .use(store)
  .use(VueDOMPurifyHTML, {
    hooks: {
      afterSanitizeAttributes: (currentNode) => {
        // Do something with the node
        // set all elements owning target to target=_blank
        if ('target' in currentNode) {
          currentNode.setAttribute('target', '_blank');
          currentNode.setAttribute('rel', 'noopener');
        }
      },
    },
  });

const vm = app.mount('#app');
export default vm;
