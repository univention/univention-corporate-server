<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    ref="tree"
    class="tree"
    role="grid"
  >
    <TransitionGroup name="list">
      <div
        v-for="node in nodes"
        :id="node.data.id"
        :key="node.data.id"
        role="row"
        :class="['tree-node', { 'tree-node--selected': node.isSelected }]"
        :style="{ paddingLeft: `${node.level * 1.2}em` }"
        @click="onNodeSelect(node)"
        @dblclick="onNodeExpand(node)"
        @contextmenu="onNodeContextMenu(node)"
      >
        <span
          v-if="!isLoading || (isLoading && !node.isSelected)"
          :class="['tree-node-arrow-icon', { 'tree-node-arrow-icon--expanded': node.isExpanded }]"
          role="gridcell"
          @click="onNodeExpand(node)"
        >
          <PortalIcon
            :icon="node.data.$childs$ ? 'chevron-right' : ''"
            role="presentation"
          />
        </span>
        <StandbyCircle
          v-if="node.isSelected && isLoading"
          class="tree-node-loading-icon"
          role="gridcell"
        />
        <span
          :class="`tree-node-icon tree-node-icon--${node.data.icon}`"
          role="gridcell"
        />
        <span role="gridcell">{{ node.data.label }}</span>
      </div>
    </TransitionGroup>
    <ContextMenu
      v-if="!isContextMenuDisabled"
      :selected-node="contextMenuSelectedNode"
      :context-menu-options="contextMenuOptions"
      @on-context-menu-option="onContextMenuOption"
    >
      <template
        v-for="(index, name) in $slots"
        :key="index"
        #[name]="data"
      >
        <slot
          v-if="name.includes('context-menu-option')"
          :name="name"
          v-bind="data"
        />
      </template>
    </ContextMenu>
  </div>
</template>

<script lang="ts">
import PortalIcon from '@/components/globals/PortalIcon.vue';
import StandbyCircle from '@/components/StandbyCircle.vue';
import { defineComponent, PropType } from 'vue';
import ContextMenu from './ContextMenu.vue';
import Node from './node';
import type { ContextMenuOption, NodeProps, OperationProps } from './types';

interface Data {
  nodes: Node[];
  isContextMenuOpen: boolean;
  contextMenuSelectedNode: Node | null;
}

export default defineComponent({
  name: 'Tree',
  components: {
    PortalIcon,
    StandbyCircle,
    ContextMenu,
  },
  props: {
    lists: {
      type: Array as PropType<NodeProps[]>,
      default: () => [],
    },
    onExpand: {
      type: Function as PropType<(node: NodeProps) => void>,
      required: true,
    },
    onCollapse: {
      type: Function as PropType<(node: NodeProps) => void>,
      required: true,
    },
    onSelect: {
      type: Function as PropType<(node: NodeProps) => void>,
      required: true,
    },
    isLoading: {
      type: Boolean as PropType<boolean>,
      default: false,
    },
    isContextMenuDisabled: {
      type: Boolean as PropType<boolean>,
      default: false,
    },
    on: {
      type: Object as PropType<OperationProps>,
    },
    contextMenuOptions: {
      type: Array as PropType<ContextMenuOption[]>,
      default: () => [],
    },
  },
  data(): Data {
    return {
      nodes: [],
      isContextMenuOpen: false,
      contextMenuSelectedNode: null,
    };
  },
  watch: {
    lists: {
      deep: true,
      handler(lists: NodeProps[]) {
        // set new nodes, but keep the old ones with the same id
        this.nodes = lists.map((newNode) => {
          const node = this.nodes.find((n) => n.data.id === newNode.id);
          if (node) {
            return node;
          }
          return new Node(newNode, null, [], false, false);
        });
        this.updateNodes();
      },
    },
    isContextMenuOpen(isOpen: boolean) {
      if (!isOpen) this.contextMenuSelectedNode = null;
    },
  },
  mounted() {
    this.nodes = this.lists.map((propNode) => new Node(propNode, null, []));

    this.updateNodes();
  },
  methods: {
    onNodeExpand(expandedNode: Node) {
      expandedNode.toggleIsExpanded();
      this.onNodeSelect(expandedNode);
      if (expandedNode.isExpanded) {
        this.onExpand(expandedNode.data);
        return;
      }
      this.onCollapse(expandedNode.data);
    },
    onNodeSelect(selectedNode: Node) {
      this.nodes.forEach((node) => {
        node.toggleIsSelected(false);
      });
      selectedNode.toggleIsSelected(true);
      this.onSelect(selectedNode.data);
    },
    updateNodes() {
      // find parent and children nodes
      this.nodes = this.nodes.map((node) => {
        const parent = this.nodes.find((n) => n.data.path === node.parentPath);
        if (parent) {
          node.parent = parent;
          parent.children.push(node);
        }
        return node;
      });

      // group nodes by parent id
      const nodesByParentId = this.nodes.reduce((acc, node) => {
        const parentId = node.parent?.data.id ?? null;
        if (!parentId) return acc;
        if (!acc[parentId]) {
          acc[parentId] = [];
        }
        acc[parentId].push(node);
        return acc;
      }, {} as Record<string, Node[]>);

      // move nodes to after their parent, also sort by level
      Object.keys(nodesByParentId).forEach((parentId) => {
        const parentNode = this.nodes.find((n) => n.data.id === parentId);
        if (!parentNode) return;
        const children = nodesByParentId[parentId];
        // sort children by label (alphabetically) descendingly
        children.sort((a, b) => {
          if (a.data.label < b.data.label) return 1;
          if (a.data.label > b.data.label) return -1;
          return 0;
        });
        // move children to after their parent
        children.forEach((child) => {
          const index = this.nodes.indexOf(child);
          if (index === -1) return;
          this.nodes.splice(index, 1);
          this.nodes.splice(this.nodes.indexOf(parentNode) + 1, 0, child);
        });
      });
    },
    onNodeContextMenu(node: Node) {
      this.contextMenuSelectedNode = node;
      this.onNodeSelect(node);
    },
    isRootNode(node: Node | null): boolean {
      return node?.parent === null;
    },
    onContextMenuOption(operationMethod: string) {
      const selectedNode = this.contextMenuSelectedNode;
      if (!selectedNode || !this.on || !this.on[operationMethod]) {
        return;
      }

      this.on[operationMethod](selectedNode.data);
    },
  },
});
</script>

<style lang="stylus">
.tree
  background-color: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  height: auto
  max-height: 30em
  overflow-y: auto
  display: flex
  flex-direction: column
  position: relative

.tree-node
  display: flex
  align-items: center
  border: none
  padding: var(--layout-spacing-unit) 0
  text-overflow: ellipsis
  white-space: nowrap
  transition: background-color 0.2s ease-in-out
  cursor: pointer

  &:hover
    background-color: var(--bgc-tree-row-hover)

  &--selected
    background-color: var(--bgc-tree-row-selected)
    &:hover
      background-color: var(--bgc-tree-row-selected)

  &-icon
    width: 16px
    height: 16px
    margin-right: 5px
    &--udm-settings-cn
      background-image: url(/data/icons/udm-settings-cn.png) !important
    &--udm-container-dc
      background-image: url(/data/icons/udm-container-dc.png) !important
    &--udm-container-ou
      background-image: url(/data/icons/udm-container-ou.png) !important
    &--udm-container-cn
      background-image: url(/data/icons/udm-container-cn.png) !important
    &--udm-dns-forward_zone
      background-image: url(/data/icons/udm-dns-forward_zone.png) !important
    &--udm-dns-reverse_zone
      background-image: url(/data/icons/udm-dns-reverse_zone.png) !important

  &-arrow-icon
    display: flex
    align-items: center
    padding: 0 var(--layout-spacing-unit)
    transition: transform 0.2s ease-in-out

    &--expanded
      transform: rotate(90deg)

  &-loading-icon
    width: 16px
    height: 16px
    padding: 0 var(--layout-spacing-unit)

.list-enter-active,
.list-leave-active
  transition: all 0.5s ease

.list-enter-from,
.list-leave-to
  opacity: 0;

</style>
