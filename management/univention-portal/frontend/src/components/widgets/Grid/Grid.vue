<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div class="grid">
    <GridHeader
      :is-any-item-selected="isAnyItemSelected"
      :item-count="gridItems.length"
      :selected-item-count="selectedItems.length"
      @on-operation="onOperation"
      @on-add-new-item="onAddNewItem"
    >
      <template #header-option-buttons>
        <slot name="header-option-buttons" />
      </template>
      <template #header-status-text="data">
        <slot
          name="header-status-text"
          v-bind="data"
        />
      </template>
    </GridHeader>
    <GridTable
      :items="gridItems"
      :columns="tableHeaderColumns"
      :on-item-selected="onItemSelected"
      @on-sort="onSort"
      @on-operation="onOperation"
    >
      <template #table-header>
        <TableHeader
          :columns="tableHeaderColumns"
          :checkbox-checked="tableHeaderCheckboxChecked"
          @update:table-header-checkbox="onTableHeaderCheckboxUpdate"
          @on-sort="onSort"
        >
          <template
            v-for="(index, name) in $slots"
            :key="index"
            #[name]="data"
          >
            <slot
              v-if="name.includes('table-header-value')"
              :name="name"
              v-bind="data"
            />
          </template>
        </TableHeader>
      </template>
      <template #table-body>
        <TableBody
          :items="gridItems"
          :columns="tableHeaderColumns"
          :on-item-selected="onItemSelected"
        >
          <template
            v-for="(index, name) in $slots"
            :key="index"
            #[name]="data"
          >
            <slot
              v-if="name.includes('table-body-value')"
              :name="name"
              v-bind="data"
            />
          </template>
        </TableBody>
      </template>
    </GridTable>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import {
  GridHeader, GridTable, TableBody, TableHeader,
} from './components';

import {
  GridItem,
  GridItemProps,
  HeaderCheckboxState,
  Operation,
  OperationProps,
  SortDirection,
  TableHeaderColumn,
  TableHeaderColumnProps,
} from './types';

interface Data {
  tableHeaderCheckboxChecked: HeaderCheckboxState;
  gridItems: GridItem[];
  tableHeaderColumns: TableHeaderColumn[];
}

export default defineComponent({
  name: 'Grid',
  components: {
    TableBody,
    TableHeader,
    GridHeader,
    GridTable,
  },
  props: {
    columns: {
      type: Array as PropType<TableHeaderColumnProps[]>,
      default: () => [],
    },
    items: {
      type: Array as PropType<GridItemProps[]>,
      default: () => [],
    },
    on: {
      type: Object as PropType<OperationProps>,
      required: true,
    },
    onAddNewItem: {
      type: Function as PropType<() => void>,
      required: true,
    },
  },
  data(): Data {
    return {
      tableHeaderCheckboxChecked: false,
      gridItems: [],
      tableHeaderColumns: [],
    };
  },
  computed: {
    isAnyItemSelected(): boolean {
      return this.gridItems.some((item) => item.selected);
    },
    isAllItemsSelected(): boolean {
      return this.gridItems.every((item) => item.selected);
    },
    selectedItems(): GridItem[] {
      return this.gridItems.filter((item) => item.selected);
    },
  },
  watch: {
    tableHeaderCheckboxChecked(state: HeaderCheckboxState) {
      if (typeof state === 'boolean') {
        this.gridItems.forEach((item) => {
          item.selected = state;
        });
      }
    },
    gridItems: {
      deep: true,
      handler() {
        if (!this.isAnyItemSelected) {
          // if no items are selected
          this.tableHeaderCheckboxChecked = false;
        } else if (!this.isAllItemsSelected) {
          // if some items are selected but not all
          this.tableHeaderCheckboxChecked = 'mixed';
        } else {
          // if all items are selected
          this.tableHeaderCheckboxChecked = true;
        }
      },
    },
  },
  mounted() {
    this.gridItems = this.items.map((item) => ({
      ...item,
      selected: false,
    }));
    // init table header columns to be displayed
    this.initTableHeaderColumns();
  },
  methods: {
    onItemSelected(item: GridItem, deselectAll = true) {
      // deselect all other items if user clicks on other parts of the row (name, value) but not the checkbox
      if (deselectAll) {
        this.gridItems.forEach((gridItem) => {
          gridItem.selected = false;
        });
      }
      item.selected = !item.selected;
    },
    initTableHeaderColumns() {
      // if user has not specified any columns, we will show all columns except any columns that have the "$" sign in their property key
      if (!this.columns || this.columns.length === 0) {
        const itemPropertyKeys = Object.keys(this.items[0]);
        this.tableHeaderColumns = itemPropertyKeys
          .filter((key) => !key.includes('$'))
          .map((key) => ({ key, label: key, isSorted: false, sortDirection: 'asc' }));
        return;
      }
      this.tableHeaderColumns = this.columns.map((column) => ({
        ...column,
        isSorted: false,
        sortDirection: 'asc',
      }));
    },
    onTableHeaderCheckboxUpdate(selected: HeaderCheckboxState) {
      this.tableHeaderCheckboxChecked = selected;
    },
    updateTableHeaderColumns(column: TableHeaderColumn) {
      this.tableHeaderColumns = this.tableHeaderColumns.map((headerColumn) => {
        const isSorted = headerColumn.key === column.key;
        let sortDirection: SortDirection = 'asc';
        if (isSorted) {
          sortDirection = column.sortDirection === 'asc' ? 'desc' : 'asc';
        }

        return {
          ...headerColumn,
          isSorted,
          sortDirection,
        };
      });
    },
    onSort(column: TableHeaderColumn) {
      this.updateTableHeaderColumns(column);

      if (this.gridItems.length && this.on?.sort) {
        this.onOperation('sort');
      } else {
        // default sort by
        const isNumeric = (n) => /^-?\d+$/.test(n);
        const parse = (s) => (isNumeric(s) ? parseInt(s, 10) : String(s).toLowerCase());
        this.gridItems.sort((a, b) => ((parse(a[column.key]) > parse(b[column.key])) ? 1 : -1));
        if (column.sortDirection !== 'asc') {
          this.gridItems.reverse();
        }
      }
    },
    onOperation(operation: Operation) {
      const selectedIds = this.selectedItems.map((item) => item.$dn$);
      // find selected items but get the original item (from props)
      const selectedPropsItems: GridItemProps[] = this.items.filter((item) => selectedIds.includes(item.$dn$));
      if (!selectedPropsItems.length || !this.on || !this.on[operation]) {
        return;
      }
      // check all selected items are need to have operation in $operations$ property, if not, don't do anything
      if (!selectedPropsItems.every((item) => item.$operations$ && item.$operations$.includes(operation))) {
        return;
      }
      this.on[operation](selectedPropsItems);
    },
  },
});
</script>
