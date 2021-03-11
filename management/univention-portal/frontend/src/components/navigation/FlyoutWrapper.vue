<template>
  <section
    :class="{ 'flyout-wrapper--isVisible': isVisible }"
    class="flyout-wrapper"
  >
    <slot />
  </section>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';

@Options({
  name: 'FlyoutWrapper',
  props: {
    isVisible: {
      type: Boolean,
      required: true,
    },
  },
})
export default class FlyoutWrapper extends Vue {}
</script>

<style lang="stylus">
.flyout-wrapper
  width: 36rem
  max-width: 36rem
  position: fixed
  top:  calc(var(--portal-header-height) + 0.5rem)
  right: 0
  z-index: 100
  background-color: var(--bgc-content-header)
  color: #fff
  transform: translate3d(110%, 0, 0)
  transition: transform cubic-bezier(0, 0, 0.2, 1) 0.5s

  &--isVisible
    transform: translate3d(0, 0, 0) scale(1, 1)
    transition: transform cubic-bezier(0, 0, 0.2, 1) 0.5s

  &__notification
    width: 36rem
    max-width: 36rem
    min-height: 100vh

  &__bubble
    padding: 0 20px
</style>
