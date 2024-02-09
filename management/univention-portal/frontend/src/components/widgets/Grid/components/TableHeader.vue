<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    class="grid-table-header-checkbox"
    role="columnheader"
  >
    <GridCheckbox
      :checked="checkboxChecked"
      :is-header="true"
      @update:checked="$emit('update:tableHeaderCheckbox', $event)"
    />
  </div>
  <div
    v-for="(column, index) in columns"
    :key="index"
    class="grid-table-header-value"
    role="columnheader"
    :style="{'width': `calc(100% + ${index * 15}px)`}"
    @click="$emit('onSort', column)"
  >
    <slot
      :name="`table-header-value-${column.key}`"
      :column="column"
    >
      <Transition>
        <PortalIcon
          v-if="column.isSorted"
          :class="['grid-table-header-sort-icon', `grid-table-header-sort-icon-${column.sortDirection}`]"
          icon="chevron-down"
          role="presentation"
        />
      </Transition>
      <span role="presentation">{{ column.label }}</span>
    </slot>
  </div>
</template>

<script lang='ts'>
import PortalIcon from '@/components/globals/PortalIcon.vue';
import { defineComponent, PropType } from 'vue';
import { HeaderCheckboxState, TableHeaderColumn } from '../types';
import GridCheckbox from './GridCheckbox.vue';

export default defineComponent({
  name: 'GridTableHeader',
  components: {
    GridCheckbox,
    PortalIcon,
  },
  props: {
    columns: {
      type: Array as PropType<TableHeaderColumn[]>,
      default: () => [],
    },
    checkboxChecked: {
      type: [Boolean, String] as PropType<HeaderCheckboxState>,
      required: true,
    },
  },
  emits: ['update:tableHeaderCheckbox', 'onSort'],
});
</script>

<style lang="stylus">
.grid-table-header
  display: flex
  padding: calc(1.5 * var(--layout-spacing-unit-small)) calc(3 * var(--layout-spacing-unit-small))
  border-bottom: 1px solid var(--bgc-content-body)
  font-size: var(--font-size-3)

  > div
    display: flex
    align-items: center

  &-checkbox
    display: flex
    align-items: center
    width: calc(6 * var(--layout-spacing-unit));
    padding-left: var(--layout-spacing-unit);
    padding-right: calc(2 * var(--layout-spacing-unit));

  &-value
    cursor: pointer

  &-sort-icon
    margin-right: 5px
    transition: transform 250ms
    &-asc
      transform: rotate(180deg)
    &-desc
      transform: rotate(0deg)
</style>
