<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
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
      class="cookie-banner-modal"
    >
      <main class="cookie-banner">
        <div
          v-dompurify-html="cookieText"
        />
      </main>
      <footer>
        <button
          ref="acceptButton"
          class="button--primary"
          @click.stop="setCookies()"
        >
          {{ ACCEPT }}
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
    domain(): string {
      let ret = document.domain;
      this.metaData.cookieBanner.domains.some((dom) => {
        if (document.domain.endsWith(dom)) {
          ret = dom;
          return true;
        }
        return false;
      });
      return ret;
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
      setCookie(this.cookieName, cookieValue, '/', this.domain);
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
  overflow-y: auto !important
  a
    color: inherit
    transition: color var(--portal-transition-duration), text-decoration-thickness var(--portal-transition-duration)
    text-decoration: underline
    text-decoration-thickness: 1px

    &:focus
      color: var(--color-accent)
      text-decoration-thickness: 3px
.cookie-banner-modal
  display: flex
  flex-direction: column
</style>
