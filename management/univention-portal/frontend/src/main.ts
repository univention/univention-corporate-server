import { createApp } from 'vue';
import App from '@/App.vue';
import { store } from '@/store';
import localize from '@/plugins/localize';

createApp(App)
  .use(store)
  .use(localize)
  .mount('#app');
