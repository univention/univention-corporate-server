<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    :class="{ 'flyout-wrapper--isVisible': isVisible }"
    class="flyout-wrapper"
  >
    <slot />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'FlyoutWrapper',
  props: {
    isVisible: {
      type: Boolean,
      required: true,
    },
  },
});
</script>

<style lang="stylus">
.flyout-wrapper
  width: 100%
  max-width: 23rem
  position: fixed
  top:  calc(var(--portal-header-height) + var(--layout-spacing-unit))
  bottom: var(--layout-spacing-unit)
  right: 0
  z-index: 100
  background-color: var(--bgc-content-container)
  transform: translate3d(110%, 0, 0)
  transition: transform cubic-bezier(0, 0, 0.2, 1) 0.15s
  border-radius: 0.5rem 0 0 0.5rem

  &--isVisible
    transform: translate3d(0, 0, 0) scale(1, 1)
    transition: transform cubic-bezier(0, 0, 0.2, 1) 0.15s
</style>
