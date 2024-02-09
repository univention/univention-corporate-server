<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <Teleport to="body">
    <div
      v-show="isOpen"
      ref="contextMenu"
      :style="{ left: `${position.x}px`, top: `${position.y}px` }"
      class="context-menu"
      role="menu"
    >
      <div
        v-for="(contextMenuOption, index) in contextMenuOptions"
        :key="index"
        class="context-menu-item"
        role="menuitem"
        :aria-label="contextMenuOption.label"
        @click="$emit('onOperation', contextMenuOption.operation)"
      >
        <PortalIcon
          :icon="contextMenuOption.icon"
          class="context-menu-item-icon"
          role="presentation"
        />
        <span role="presentation">
          {{ contextMenuOption.label }}
        </span>
      </div>
    </div>
  </Teleport>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import { ContextMenuOption } from '../types';

export default defineComponent({
  name: 'GridContextMenu',
  components: {
    PortalIcon,
  },
  props: {
    contextMenuOptions: {
      type: Array as PropType<ContextMenuOption[]>,
      required: true,
    },
    position: {
      type: Object as PropType<{ x: number; y: number }>,
      required: true,
    },
    isOpen: {
      type: Boolean as PropType<boolean>,
      required: true,
    },
    parentElement: {
      type: String as PropType<string | null>,
      default: null,
    },
    disableRightClick: {
      type: Boolean as PropType<boolean>,
      default: false,
    },
  },
  emits: ['onOperation', 'onOpen', 'onOutsideClick'],
  mounted() {
    if (!this.disableRightClick) {
      this.setUpContextMenu();
    }
    document.addEventListener('click', this.detectOutsideClick);
  },
  unmounted() {
    document.removeEventListener('click', this.detectOutsideClick);
  },
  methods: {
    setUpContextMenu() {
      const parent = this.$parent;
      if (!parent) return;
      const parentElement = parent.$el as HTMLDivElement;

      parentElement.addEventListener('contextmenu', (e: MouseEvent) => {
        const elementClicked = e.target as HTMLElement;

        if (this.parentElement && !elementClicked.className.includes(this.parentElement)) {
          this.$emit('onOutsideClick');
          return;
        }
        e.preventDefault();
        e.stopPropagation();

        // set position of context menu
        const x: number = e.pageX;
        const y: number = e.pageY;
        this.$emit('onOpen', { x, y });
      });
    },
    detectOutsideClick(event: MouseEvent) {
      const contextMenuElement = this.$refs.contextMenu && this.$refs.contextMenu as HTMLDivElement;
      if (contextMenuElement && !contextMenuElement.contains(event.target as HTMLElement) && this.isOpen) {
        this.$emit('onOutsideClick', event);
      }
    },
  },
});
</script>

<style lang="stylus">
.context-menu
  position: absolute
  z-index: 10
  background-color: var(--bgc-popup)
  border-radius: var(--border-radius-container)
  &-item
    display: flex
    align-items: center
    padding: 0.3rem 0.75rem
    cursor: pointer
    transition: background-color 250ms
    &:hover
      background-color: var(--bgc-popup-item-hover)
    &-icon
      height: var(--button-icon-size)
      width: var(--button-icon-size)
      padding-left: 0.2rem
      padding-right: 0.5rem
    &[aria-disabled="true"]
      cursor: not-allowed
      opacity: 0.5
      &:hover
        background-color: var(--bgc-popup-item-disabled)

</style>
