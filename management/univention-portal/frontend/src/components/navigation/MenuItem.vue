<template>
  <a
    v-is="isLink ? 'a' : 'div'"
    v-if="isVisible"
    class="menu-item"
    :href="link"
    @click="tileClick"
  >
    <portal-icon
      v-if="subItem"
      icon="chevron-left"
      icon-width="2rem"
      class="menu-item__arrow menu-item__arrow--left"
    />
    {{ $localized(title) }}
    <template
      v-if="subMenu.length > 0"
    >
      <div
        class="menu-item__counter"
      >
        {{ subMenu.length }}
      </div>
      <portal-icon
        v-if="!subItem"
        icon="chevron-right"
        icon-width="2rem"
        class="menu-item__arrow menu-item__arrow--right"
      />
    </template>
  </a>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import TileClick from '@/mixins/TileClick.vue';

export default defineComponent({
  name: 'MenuItem',
  components: {
    PortalIcon,
  },
  mixins: [
    TileClick,
  ],
  props: {
    title: {
      type: Object,
      required: true,
    },
    subMenu: {
      type: Array,
      default: () => [],
    },
    subItem: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    isVisible(): boolean {
      return this.isLink || this.subItem || this.subMenu.length > 0;
    },
    isLink(): boolean {
      return !!this.link;
    },
  },
});
</script>

<style lang="stylus">
.menu-item
  position: relative;
  z-index: 15;
  display: flex;
  align-items: center;
  padding: 2rem 0 2rem 2rem;
  color: #fff;
  text-decoration: none;

  &:hover
    background-color: #272726;
    cursor: pointer;

  &__counter
    position: absolute;
    right: 0;
    margin-right: 4rem;
    display: inline;

  &__arrow
    position: absolute;
    display: inline;
    font-size: inherit;
    width: 2rem;
    height: 2rem;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    fill: none;
    transition: color 250ms;
    &--left
      left: 1.2rem;
    &--right
      right: 0;
      margin-right: 1.2rem;
</style>
