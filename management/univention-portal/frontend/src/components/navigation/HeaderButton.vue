<template>
  <div
    :class="{ 'header-button--is-active': isActiveButton }"
    class="header-button"
    @click="toggleActiveButton"
  >
    <span
      :class="'header-button__inner'"
      role="presentation"
    >
      <button
        :ref="setRef"
        :aria-expanded="isActiveButton"
        :aria-label="ariaLabel"
        :class="['header-button__button', hoverClass]"
      >
        <portal-icon
          :icon="icon"
          icon-width="2rem"
        />
      </button>
    </span>
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import PortalIcon from '@/components/globals/PortalIcon.vue';

@Options({
  name: 'HeaderButton',
  components: {
    PortalIcon,
  },
  props: {
    icon: {
      type: String,
      required: true,
    },
    ariaLabel: {
      type: String,
      required: true,
    },
    noClick: {
      type: Boolean,
      default: false,
    },
    hoverClass: {
      type: String,
      default: '',
    },
  },
  methods: {
    toggleActiveButton() {
      if (!this.noClick) {
        if (this.isActiveButton) {
          this.$store.dispatch('navigation/setActiveButton', '');
        } else {
          this.$store.dispatch('navigation/setActiveButton', this.icon);
        }
      }
    },
  },

  computed: {
    isActiveButton() {
      return this.$store.state.navigation.activeButton === this.icon;
    },
    setRef() {
      return `${this.icon}Reference`;
    },
  },
})
export default class HeaderButton extends Vue {}
</script>

<style lang="stylus">
.header-button
  --font-size-button-icon: var(--font-size-big)
  margin: 0 var(--layout-spacing-unit-small)
  --bgc: transparent
  --bgc-state: transparent
  box-shadow: none
  border-radius: var(--button-icon-border-radius)

  &--is-active
      z-index:1000

      svg
        color: var(--color-primary)

  &__inner
    border: none
    border-radius: inherit
    display: flex
    align-items: center
    justify-content: center
    transition: var(--button-bgc-transition)
    background-color: var(--bgc-state)
    transition: opacity 250ms
    font-size: var(--button-font-size)

  &__button
    width: 4rem
    height: 4rem
    background: none
    border: none
    color: white
    display: flex
    align-items: center
    justify-content: center
    background-color: transparent

    &:hover,
    &:focus
      border-radius: 100%
      background-color: var(--bgc-content-body)

    &--success
      &:hover,
      &:focus
        background-color: var(--notification-success)

    &--warning
      &:hover,
      &:focus
        background-color: var(--notification-warning)

    &--error
      &:hover,
      &:focus
        background-color: var(--notification-error)

    &:hover
      cursor: pointer
</style>
