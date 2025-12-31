<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    v-if="displayCondition"
    class="input-error-message"
  >
    <template v-if="displayCondition">
      <portal-icon
        icon="alert-circle"
        class="input-error-message__icon"
      />
      <span>
        {{ errorMessage }}
      </span>
    </template>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'InputErrorMessage',
  components: {
    PortalIcon,
  },
  props: {
    errorMessage: {
      type: String,
      required: true,
    },
    displayCondition: {
      type: Boolean,
      required: true,
    },
  },
});
</script>

<style lang="stylus">
.input-error-message
    display: flex
    align-items: center
    color: var(--font-color-error)
    margin-bottom: var(--layout-spacing-unit)

    &__icon
        flex: 0 0 auto
        margin-right: var(--layout-spacing-unit-small)
        color: var(--font-color-error)
</style>
