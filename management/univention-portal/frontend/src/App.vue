<template>
  <home />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import Home from '@/views/Home.vue';
import { login } from '@/jsHelper/login';
import { catalog } from '@/i18n/translations';
import { Locale } from './store/models';

// get env vars
const defaultPortalLocale: Locale = process.env.VUE_APP_LOCALE || 'en_US';

export default defineComponent({
  name: 'App',
  components: {
    Home,
  },
  mounted() {
    this.$store.dispatch('locale/setLocale', defaultPortalLocale).then(() => {
      this.$store.dispatch('loadPortal').then((PortalData) => {
        if (!PortalData.user) {
          this.$store.dispatch('notificationBubble/addNotification', {
            bubbleTitle: catalog.LOGIN.translated,
            bubbleDescription: catalog.LOGIN_REMINDER_DESCRIPTION.translated,
            onClick: () => login(this.$store.getters['user/userState']),
          });
        }
        setTimeout(() => {
          // Hide notification bubble
          this.$store.dispatch('notificationBubble/setHideNewBubble');
        }, 4000);
      });
    });
  },
});
</script>
