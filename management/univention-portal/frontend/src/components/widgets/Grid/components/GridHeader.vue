<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div class="grid-header">
    <div
      class="grid-header-button"
    >
      <slot name="header-option-buttons">
        <TransitionGroup>
          <button
            v-for="(button, index) in optionButtons"
            :key="index"
            :class="`grid-header-button--${button.label.toLowerCase()}`"
            @click="onOperation(button.operation)"
          >
            <PortalIcon
              :icon="button.icon"
              role="presentation"
            />
            <span role="presentation">{{ button.label }}</span>
          </button>
        </TransitionGroup>
      </slot>
    </div>
    <div
      class="grid-header-status"
      role="presentation"
    >
      <slot
        name="header-status-text"
        class="grid-header-status--text"
        :selected-item-count="selectedItemCount"
      >
        {{ selectedItemCountMessage }} of {{ itemCount }} selected
      </slot>
    </div>
    <ContextMenu
      :is-open="isContextMenuOpen"
      :context-menu-options="contextMenuOptions"
      :position="contextMenuPosition"
      parent-element="grid-header-button--more"
      :disable-right-click="true"
      @on-outside-click="onContextMenuOutsideClick"
      @on-operation="onOperation"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import _ from '@/jsHelper/translate';
import { ContextMenuOption, Operation } from '../types';
import ContextMenu from './ContextMenu.vue';

type OptionButtonOperation = Operation | 'more';
interface OptionButton extends Omit<ContextMenuOption, 'operation'> {
  operation: OptionButtonOperation;
}

export default defineComponent({
  name: 'GridHeader',
  components: {
    PortalIcon,
    ContextMenu,
  },
  props: {
    isAnyItemSelected: {
      type: Boolean as PropType<boolean>,
      required: true,
    },
    selectedItemCount: {
      type: Number as PropType<number>,
      required: true,
    },
    itemCount: {
      type: Number as PropType<number>,
      required: true,
    },
  },
  emits: ['onOperation', 'onOutsideClick', 'onAddNewItem'],
  data() {
    return {
      isContextMenuOpen: false,
      contextMenuOptions: [
        { label: _('Edit in new tab'), icon: '', operation: 'edit' },
        { label: _('Move to...'), icon: '', operation: 'move' },
        { label: _('Copy'), icon: '', operation: 'copy' },
        { label: _('Create report'), icon: 'file-text', operation: 'search' },
      ],
      contextMenuPosition: {
        x: 0, y: 0,
      },
    };
  },
  computed: {
    optionButtons(): OptionButton[] {
      if (!this.isAnyItemSelected) {
        return [
          { label: _('Add'), icon: 'plus', operation: 'add' },
        ];
      }

      return [
        { label: _('Add'), icon: 'plus', operation: 'add' },
        { label: _('Edit'), icon: 'edit-2', operation: 'edit' },
        { label: _('Delete'), icon: 'trash', operation: 'remove' },
        { label: _('More'), icon: 'more-horizontal', operation: 'more' },
      ];
    },

    selectedItemCountMessage(): string | number {
      if (this.selectedItemCount === 1) return 'One row';
      return `${this.selectedItemCount} rows`;
    },
  },
  methods: {
    onOperation(operation: OptionButtonOperation) {
      if (operation === 'more') {
        this.onMoreButtonClick();
        return;
      }
      if (operation === 'add') {
        this.$emit('onAddNewItem');
        return;
      }
      this.$emit('onOperation', operation);
    },
    onMoreButtonClick() {
      // get more button position
      const moreButton = document.querySelector('.grid-header-button--more') as HTMLButtonElement;
      const rect = moreButton.getBoundingClientRect();
      const x = rect.left;
      const y = rect.top + rect.height;
      this.onOpenContextMenu({ x, y });
    },
    onOpenContextMenu(position: {x: number, y: number}) {
      this.contextMenuPosition = position;
      this.isContextMenuOpen = true;
    },
    onContextMenuOutsideClick(event: MouseEvent) {
      const moreButton = document.querySelector('.grid-header-button--more') as HTMLButtonElement;
      const target = event.target as HTMLElement;
      if (!moreButton.contains(target)) {
        this.isContextMenuOpen = false;
        return;
      }
      if (!this.isContextMenuOpen) {
        this.onMoreButtonClick();
      }
    },
  },
});
</script>

<style lang="stylus">
.grid-header
  display: flex
  justify-content: space-between
  align-items: center
  padding: var(--layout-spacing-unit)
  width: 100%

  &-button
    display: flex
    align-items: center
    width: 100%

    & button
      background-color: var(--button-text-bgc)
      padding: 0 var(--layout-spacing-unit)
      &:hover
        background-color: var(--button-text-bgc-hover)

  &-status
    display: flex
    align-items: center
    justify-content: right
    padding-right: calc(var(--layout-spacing-unit) * 2)
    width: 100%
    &--text
      white-space: nowrap
      overflow: hidden
      text-overflow: ellipsis
</style>
