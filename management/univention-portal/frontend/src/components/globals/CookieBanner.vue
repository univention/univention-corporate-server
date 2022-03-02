<!--
  Copyright 2021-2022 Univention GmbH

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
    :teleport-to-body="false"
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
          ref="acceptButton"
          class="primary"
          @click.stop="setCookies()"
        >
          <span>
            {{ ACCEPT }}
          </span>
        </button>
      </footer>
    </modal-dialog>
  </modal-wrapper>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import ModalDialog from '@/components/modal/ModalDialog.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';

import { setCookie } from '@/jsHelper/tools';

export default defineComponent({
  name: 'CookieBanner',
  components: {
    ModalWrapper,
    ModalDialog,
  },
  emits: ['dismissed'],
  computed: {
    ...mapGetters({ metaData: 'metaData/getMeta' }),
    cookieName(): string {
      return this.metaData.cookieBanner.cookie || 'univentionCookieSettingsAccepted';
    },
    cookieTitle(): string {
      return this.$localized(this.metaData.cookieBanner.title) || _('Cookie Settings');
    },
    cookieText(): string {
      return this.$localized(this.metaData.cookieBanner.text) || _('We use cookies in order to provide you with certain functions and to be able to guarantee an unrestricted service. By clicking on "Accept", you consent to the collection of information on this portal.');
    },
    ACCEPT(): string {
      return _('Accept');
    },
  },
  mounted(): void {
    this.$store.dispatch('activity/setLevel', 'cookies');
    // @ts-ignore
    this.$refs.acceptButton.focus();
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

<style lang="stylus">
.cookie-banner
  a
    color: inherit
    transition: color var(--portal-transition-duration), text-decoration-thickness var(--portal-transition-duration)
    text-decoration: underline
    text-decoration-thickness: 1px

    &:focus
      color: var(--color-accent)
      text-decoration-thickness: 3px
</style>
