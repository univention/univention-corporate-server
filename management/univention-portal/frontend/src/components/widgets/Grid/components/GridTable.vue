<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    class="grid-table"
    role="grid"
  >
    <div
      class="grid-table-header"
      role="row"
    >
      <slot
        name="table-header"
      />
    </div>
    <div class="grid-table-body">
      <slot name="table-body" />
    </div>
    <ContextMenu
      :is-open="isContextMenuOpen"
      :context-menu-options="contextMenuOptions"
      :position="contextMenuPosition"
      parent-element="grid-table-body"
      @on-open="onOpenContextMenu"
      @on-outside-click="isContextMenuOpen = false"
      @on-operation="(operation) => $emit('onOperation', operation)"
    />
  </div>
</template>

<script lang="ts">
import _ from '@/jsHelper/translate';
import { GridItem, TableHeaderColumn } from 'components/widgets/Grid/types';
import { defineComponent, PropType } from 'vue';
import ContextMenu from './ContextMenu.vue';
import TableHeader from './TableHeader.vue';
import TableBody from './TableBody.vue';

export default defineComponent({
  name: 'GridTable',
  components: {
    ContextMenu,
    TableHeader,
    TableBody,
  },
  props: {
    columns: {
      type: Array as PropType<TableHeaderColumn[]>,
      default: () => [],
    },
    items: {
      type: Array as PropType<GridItem[]>,
      required: true,
    },
    onItemSelected: {
      type: Function as PropType<(item: GridItem, deselectAll?: boolean) => void>,
      required: true,
    },
  },
  emits: ['onOperation', 'onSort'],
  data() {
    return {
      isContextMenuOpen: false,
      contextMenuOptions: [
        { label: _('Edit'), icon: 'edit-2', operation: 'edit' },
        { label: _('Delete'), icon: 'trash', operation: 'remove' },
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
  methods: {
    onOpenContextMenu(position: {x: number, y: number}) {
      this.contextMenuPosition = position;
      this.isContextMenuOpen = true;
    },
  },
});
</script>

<style lang="stylus">
.grid-table
  width: 100%
  border-top: 1px solid var(--bgc-content-body)

</style>
