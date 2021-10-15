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
  <cookie-banner
    v-if="showCookieBanner"
    @dismissed="hideCookieBanner"
  />
  <portal />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import Portal from '@/views/Portal.vue';
import CookieBanner from '@/components/globals/CookieBanner.vue';

import { getCookie } from '@/jsHelper/tools';
import { login } from '@/jsHelper/login';
import { mapGetters } from 'vuex';

interface AppData {
  cookieBannerDismissed: boolean,
}

export default defineComponent({
  name: 'App',
  components: {
    Portal,
    CookieBanner,
  },
  data(): AppData {
    return {
      cookieBannerDismissed: false,
    };
  },
  computed: {
    ...mapGetters({
      userState: 'user/userState',
      metaData: 'metaData/getMeta',
    }),
    showCookieBanner(): boolean {
      const cookieName = this.metaData.cookieBanner.cookie || 'univentionCookieSettingsAccepted';
      return this.metaData.cookieBanner.show && !getCookie(cookieName) && !this.cookieBannerDismissed;
    },
  },
  async mounted() {
    // Set locale and load portal data from backend
    this.$store.dispatch('activateLoadingState');
    const answer = await this.$store.dispatch('loadPortal', {
      adminMode: false,
    });

    if (answer.portal && answer.portal.ensureLogin && !this.userState.username) {
      login(this.userState);
    }

    this.$store.dispatch('deactivateLoadingState');
  },
  methods: {
    hideCookieBanner(): void {
      this.cookieBannerDismissed = true;
    },
  },
});
</script>

<style>
</style>
