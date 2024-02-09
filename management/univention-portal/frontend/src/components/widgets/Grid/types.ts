/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

// mixed is when some items are selected but not all
// so the checkbox will show a minus sign (-) instead of a checkmark (✓)
// when the checkbox with the minus sign is clicked, all items will be deselected
export type HeaderCheckboxState = boolean | 'mixed';

export type Operation = 'add' | 'edit' | 'remove' | 'search' | 'move' | 'copy' | 'sort';

export type SortDirection = 'asc' | 'desc';

export interface ContextMenuOption {
  label: string;
  icon: string;
  operation: Operation;
}

export interface TableHeaderColumnProps {
  label: string;
  key: string;
}

export interface TableHeaderColumn extends TableHeaderColumnProps {
  isSorted: boolean;
  sortDirection: SortDirection;
}

export interface GridColumnProps {
  order?: number;
  name: string;
  label?: string;
}

export interface GridItemProps {
  $dn$: string;
  $childs$: boolean;
  $flags$: string[];
  $operations$: Operation[];
  objectType: string;
  labelObjectType: string;
  name: string;
  path: string;
}

export interface GridItem extends GridItemProps {
  selected: boolean;
}

export interface OperationProps {
  [operation: string]: (items: GridItemProps[]) => void;
}
