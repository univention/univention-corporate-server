<!--
Copyright 2021 Univention GmbH

https://www.univention.de/

All rights reserved.

The source code of this program is made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use this program under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/>.
-->
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

    if (!portalData.username) {
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
