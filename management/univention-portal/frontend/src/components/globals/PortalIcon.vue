<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <svg
    class="portal-icon"
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    aria-hidden="true"
  >
    <use :xlink:href="`feather-sprite.svg#${icon}`" />
  </svg>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'PortalIcon',
  props: {
    icon: {
      type: String,
      required: true,
    },
  },
});
</script>

<style lang="stylus">
.portal-icon
  font-size: inherit
  height: var(--button-icon-size)
  width: var(--button-icon-size)
  stroke: currentColor
  stroke-width: 2
  stroke-linecap: round
  stroke-linejoin: round
  color: var(--font-color-contrast-high)
  fill: none
  transition: color var(--portal-transition-duration)
</style>
