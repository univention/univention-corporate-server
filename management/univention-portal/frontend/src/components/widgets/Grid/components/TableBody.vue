<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    v-for="(item, index) in items"
    :key="item.name"
    class="grid-table-body-row"
    role="row"
    @contextmenu="onContextMenuSelect(item)"
  >
    <div
      class="grid-table-body-row-checkbox"
      role="gridcell"
      @click="onItemSelected(item, false)"
    >
      <GridCheckbox :checked="item.selected" />
    </div>
    <div
      v-for="column in columns"
      :key="column.key"
      role="gridcell"
      class="grid-table-body-row-value"
    >
      <slot
        :name="`table-body-value-${column.key}-${index}`"
        :item="item"
        class="grid-table-body-row-value"
        @click="onItemSelected(item)"
      >
        {{ item[column.key] }}
      </slot>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { GridItem, TableHeaderColumn } from '../types';
import GridCheckbox from './GridCheckbox.vue';

export default defineComponent({
  name: 'GridTableBody',
  components: {
    GridCheckbox,
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
  methods: {
    onContextMenuSelect(item: GridItem) {
      // if the item is already selected, we don't want to deselect it
      if (item.selected) return;
      // otherwise select the item
      this.onItemSelected(item);
    },
  },
});
</script>

<style lang="stylus">
.grid-table-body
  width: 100%
  max-height: 30em
  overflow: auto

  &-row
    display: flex
    align-items: center
    padding: calc(1.5 * var(--layout-spacing-unit-small)) calc(3 * var(--layout-spacing-unit-small))
    border-bottom: 1px solid var(--bgc-content-body)
    transition: all 250ms

    > div
      display: flex
      align-items: center

    &-checkbox
      width: calc(6 * var(--layout-spacing-unit))
      padding-left: var(--layout-spacing-unit)
      padding-right: calc(2 * var(--layout-spacing-unit))

    &-name, &-value
      width: 100%

    &:hover
      background-color: var(--bgc-grid-row-hover)

</style>
