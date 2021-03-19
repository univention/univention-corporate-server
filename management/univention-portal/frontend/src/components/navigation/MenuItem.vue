<template>
  <a
    v-is="isLink ? 'a' : 'div'"
    class="menu-item"
    :href="link ? link : null"
    tabindex="0"
    @click="isInternalFunctionOrLink ? tileClick() : null"
    @keydown.enter="isInternalFunctionOrLink ? tileClick() : null"
    @keydown.esc="closeWithESC"
  >
    <portal-icon
      v-if="isSubItem"
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
        v-if="!isSubItem"
        icon="chevron-right"
        icon-width="2rem"
        class="menu-item__arrow menu-item__arrow--right"
      />
    </template>
  </a>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import TileClick from '@/mixins/TileClick.vue';
import { Locale } from '@/store/models';

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
      type: Object as PropType<Record<Locale, string>>,
      required: true,
    },
    subMenu: {
      type: Array,
      default: () => [],
    },
    isSubItem: {
      type: Boolean,
      default: false,
    },
    handlesAppSettings: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['clickAction'],
  computed: {
    isInternalFunctionOrLink(): boolean {
      return this.linkTarget === 'internalFunction' || this.isLink;
    },
    isLink(): boolean {
      return this.link !== null && this.link !== '';
    },
  },
  methods: {
    closeWithESC() {
      this.$emit('clickAction');
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
  border: 0.2rem solid rgba(0,0,0,0);

  &:hover
    background-color: #272726;
    cursor: pointer;

  &:focus
    outline: 0;
    border: 0.2rem solid var(--color-primary);

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
