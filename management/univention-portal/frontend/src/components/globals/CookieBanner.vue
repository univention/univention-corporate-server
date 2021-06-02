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
  <modal-wrapper
    :is-active="true"
    :full="true"
  >
    <modal-dialog
      :title="cookieTitle"
      :cancel-allowed="false"
    >
      <main class="cookie-banner">
        <div
          v-dompurify-html="cookieText"
        />
      </main>
      <footer>
        <button
          class="primary"
          @click.stop="setCookies()"
        >
          <translate i18n-key="ACCEPT" />
        </button>
      </footer>
    </modal-dialog>
  </modal-wrapper>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import Translate from '@/i18n/Translate.vue';
import ModalDialog from '@/components/ModalDialog.vue';
import ModalWrapper from '@/components/globals/ModalWrapper.vue';

import { setCookie } from '@/jsHelper/tools';

export default defineComponent({
  name: 'CookieBanner',
  components: {
    ModalWrapper,
    ModalDialog,
    Translate,
  },
  emits: ['dismissed'],
  computed: {
    ...mapGetters({ metaData: 'metaData/getMeta' }),
    cookieName(): string {
      return this.metaData.cookieBanner.cookie || 'univentionCookieSettingsAccepted';
    },
    cookieTitle(): string {
      return this.$localized(this.metaData.cookieBanner.title) || this.$translateLabel('COOKIE_TITLE');
    },
    cookieText(): string {
      return this.$localized(this.metaData.cookieBanner.text) || this.$translateLabel('COOKIE_TEXT');
    },
  },
  mounted(): void {
    this.$store.dispatch('activity/setLevel', 'cookies');
  },
  methods: {
    setCookies(): void {
      const cookieValue = 'do-not-change-me';
      setCookie(this.cookieName, cookieValue);
      this.dismissCookieBanner();
    },
    dismissCookieBanner(): void {
      this.$store.dispatch('activity/setLevel', 'portal');
      this.$emit('dismissed');
    },
  },
});
</script>
