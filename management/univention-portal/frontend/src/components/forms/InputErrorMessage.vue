<template>
  <div
    v-if="displayCondition"
    class="input-error-message"
  >
    <portal-icon
      icon="alert-circle"
      class="input-error-message__icon"
    />
    <span>
      {{ errorMessage }}
    </span>
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
    color: var(--font-color-contrast-middle)
    margin-bottom: var(--layout-spacing-unit)

    &__icon
        margin-right: var(--layout-spacing-unit-small)
        color: var(--font-color-contrast-middle)
</style>
