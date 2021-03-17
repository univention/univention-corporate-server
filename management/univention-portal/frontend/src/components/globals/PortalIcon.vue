<template>
  <svg
    class="portal-icon"
    :width="iconWidth"
    :height="setIconHeight"
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
    iconWidth: {
      type: String,
      required: true,
    },
    iconHeight: {
      type: String,
      default: '',
      required: false,
    },
  },
  computed: {
    setIconHeight(): string {
      return this.iconHeight ? this.iconHeight : this.iconWidth;
    },
  },
});
</script>

<style lang="stylus">
.portal-icon
  font-size: inherit;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  color: var(--font-color-contrast-high);
  fill: none;
  transition: color 250ms;
</style>
