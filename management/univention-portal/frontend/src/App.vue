<template>
  <portal />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import Portal from '@/views/Portal.vue';
import { login } from '@/jsHelper/login';
import { catalog } from '@/i18n/translations';
import { mapGetters } from 'vuex';
import { Locale } from './store/models';

const defaultPortalLocale: Locale = process.env.VUE_APP_LOCALE || 'en_US';

export default defineComponent({
  name: 'App',
  components: {
    Portal,
  },
  computed: {
    ...mapGetters({
      bubbleContent: 'notificationBubble/bubbleContent',
      userState: 'user/userState',
    }),
  },
  async mounted() {
    this.$store.dispatch('modal/setShowLoadingModal');

    // Set locale and load portal data from backend
    await this.$store.dispatch('locale/setLocale', defaultPortalLocale);
    const portalData = await this.$store.dispatch('loadPortal');

    this.$store.dispatch('modal/setHideModal');

    if (!portalData.user) {
      // Display notification bubble with login reminder
      this.$store.dispatch('notificationBubble/addNotification', {
        bubbleTitle: catalog.LOGIN.translated.value,
        bubbleDescription: catalog.LOGIN_REMINDER_DESCRIPTION.translated.value,
        onClick: () => login(this.userState),
      });
      setTimeout(() => {
      // Hide notification bubble after 4 seconds
        this.$store.dispatch('notificationBubble/setHideNewBubble');
      }, 4000);
    }
  },
});
</script>
