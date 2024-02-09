<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <Teleport to="body">
    <div
      v-show="isContextMenuOpen"
      ref="contextMenu"
      class="context-menu"
      role="menu"
    >
      <div
        v-for="(contextMenuOption, index) in getContextMenuFromOperation()"
        :key="index"
        class="context-menu-item"
        role="menuitem"
        :aria-label="contextMenuOption.label"
        :aria-disabled="isOptionDisabled(contextMenuOption)"
        @click="onContextMenuOptionClick(contextMenuOption)"
      >
        <slot
          :name="`context-menu-option-${contextMenuOption.operation}`"
          :option="contextMenuOption"
        >
          <PortalIcon
            :icon="contextMenuOption.icon"
            class="context-menu-item-icon"
            role="presentation"
          />
          <span role="presentation">
            {{ contextMenuOption.label }}
          </span>
        </slot>
      </div>
    </div>
  </Teleport>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import type { ContextMenuOption, Operation } from './types';
import Node from './node';

export default defineComponent({
  components: {
    PortalIcon,
  },
  props: {
    selectedNode: {
      type: Object as PropType<Node>,
      required: true,
    },
    contextMenuOptions: {
      type: Array as PropType<ContextMenuOption[]>,
      default: () => [],
      required: true,
    },
  },
  emits: ['onContextMenuOption'],
  data() {
    return {
      isContextMenuOpen: false,
    };
  },
  mounted() {
    console.log('WTF', this);
    this.setUpContextMenu();
    document.addEventListener('click', this.detectOutsideClickContextMenu);
  },
  unmounted() {
    document.removeEventListener('click', this.detectOutsideClickContextMenu);
  },
  methods: {
    setUpContextMenu() {
      const tree = this.$parent;
      if (!tree) return;
      // prevent right click in refs.tree
      const treeElement = tree.$el as HTMLDivElement;
      const contextMenuElement = this.$refs.contextMenu as HTMLDivElement;
      treeElement.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.isContextMenuOpen = true;
        // set position of context menu
        contextMenuElement.style.left = `${e.pageX}px`;
        contextMenuElement.style.top = `${e.pageY}px`;
      });
    },
    detectOutsideClickContextMenu(event: MouseEvent) {
      const contextMenuElement = this.$refs.contextMenu as HTMLDivElement;
      if (
        !contextMenuElement.contains(event.target as HTMLElement) &&
        this.isContextMenuOpen
      ) {
        this.isContextMenuOpen = false;
      }
    },
    isOptionDisabled(contextMenuOption: ContextMenuOption): boolean {
      const selectedNode = this.selectedNode;
      if (!selectedNode) {
        return true;
      }
      // always allow reload option
      if (contextMenuOption.operation === 'reload') {
        return false;
      }

      const availableOperations = selectedNode.data.$operations$;
      // disable the option if the operation of the selected node doesn't have the operation of the context menu option
      return !availableOperations.includes(contextMenuOption.operation);
    },
    getContextMenuFromOperation(): ContextMenuOption[] {
      const operation: Operation[] = this.selectedNode && this.selectedNode.data.$operations$;
      return this.contextMenuOptions.filter((option) => operation && operation.includes(option.operation));
    },
    onContextMenuOptionClick(contextMenuOption: ContextMenuOption) {
      const selectedNode = this.selectedNode;
      if (!selectedNode) return;
      if (this.isOptionDisabled(contextMenuOption)) return;
      this.isContextMenuOpen = false;
      this.$emit('onContextMenuOption', contextMenuOption.operation);
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
    padding: 0.3rem 1.2rem
    cursor: pointer
    transition: background-color 0.15s
    &:hover
      background-color: var(--bgc-popup-item-hover)

    &-icon
      height: var(--button-icon-size)
      width: var(--button-icon-size)
      padding-left: 0.1rem
      padding-right: 0.5rem

    &[aria-disabled="true"]
      cursor: not-allowed
      opacity: 0.5
      &:hover
        background-color: var(--bgc-popup-item-disabled)

</style>
