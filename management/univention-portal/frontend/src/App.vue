<template>
  <home />
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import { store } from '@/store';
import { catalog } from '@/i18n/translations';
import Home from '@/views/Home.vue';

// get env vars
const defaultPortalLocale = process.env.VUE_APP_LOCALE || 'en_US';

@Options({
  name: 'App',

  components: {
    Home,
  },
  mounted() {
    store.dispatch('locale/setLocale', { locale: defaultPortalLocale }).then(() => {
      store.dispatch('loadPortal').then((PortalData) => {
        if (!PortalData.user) {
          store.dispatch('notificationBubble/addNotification', {
            bubbleTitle: catalog.LOGIN.translated,
            bubbleDescription: catalog.LOGIN_REMINDER_DESCRIPTION.translated,
          });
        }
        setTimeout(() => {
          // Hide notification bubble
          store.dispatch('notificationBubble/setHideNewBubble');
        }, 4000);
      });
    });
  },
})

export default class App extends Vue {
  store: typeof store = store;
}
</script>
