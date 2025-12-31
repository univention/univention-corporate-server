<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <main class="portal-error">
    <h1 class="portal-error__title">
      {{ ERROR_MESSAGE }}
    </h1>
    <p class="portal-error__text">
      {{ ERROR_SUBTEXT }}
    </p>
  </main>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

export default defineComponent({
  name: 'Portalerror',
  props: {
    errorType: {
      type: Number,
      required: true,
    },
  },
  computed: {
    ERROR_MESSAGE(): string {
      if (this.errorType === 404) {
        return _('Page not found');
      }
      return _('Sorry.');
    },
    ERROR_SUBTEXT(): string {
      if (this.errorType === 404) {
        return _('This URL does not exist (anymore).');
      }
      return _('The portal is temporarily unavailable. If the problem persists, please contact your system administrator.');
    },
  },
  mounted() {
    this.$store.dispatch('activity/setMessage', `${this.ERROR_MESSAGE}. ${this.ERROR_SUBTEXT}`);
  },
});
</script>
<style lang="stylus">
.portal-error
  position: relative
  display: flex
  flex-direction: column
  margin-left: calc(2 * var(--layout-spacing-unit) + var(--layout-spacing-unit) + 0.2rem)

  @media $mqSmartphone
    margin-left: 1em

  &__title
    margin-bottom: 0
</style>
