<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    v-show="isActive"
    class="portal-iframe"
  >
    <span
      class="portal-iframe__status"
    />
    <iframe
      :id="`iframe-${tabId + 1}`"
      ref="iframe"
      :src="link"
      :title="title"
      :tabindex="tabindex"
      class="portal-iframe__iframe"
      allow="geolocation; microphone; camera; midi; encrypted-media"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'PortalIframe',
  props: {
    link: {
      type: String,
      required: true,
    },
    isActive: {
      type: Boolean,
      default: false,
    },
    tabId: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      activeButton: 'navigation/getActiveButton',
    }),
    tabindex(): number {
      return this.activeButton === 'copy' ? -1 : 0;
    },
  },
  mounted() {
    (this.$refs.iframe as HTMLIFrameElement).contentWindow?.focus();
  },
  updated() {
    if (this.isActive && this.activeButton === '') {
      (this.$refs.iframe as HTMLIFrameElement).contentWindow?.focus();
    }
  },
});
</script>

<style lang="stylus">
.portal-iframe
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;

  &__iframe
    position: relative;
    border: none;
    width: 100%;
    height: 100%;

</style>
