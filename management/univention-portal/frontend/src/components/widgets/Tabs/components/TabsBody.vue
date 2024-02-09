<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<script lang="ts">
import { defineComponent, VNode, h } from 'vue';
import type { Tab } from '../types';

export default defineComponent({
  name: 'TabsBody',
  computed: {
    parent(): any {
      return this.$parent as any;
    },
    tabs(): Tab[] {
      if (this.parent && this.parent.tabs) {
        return this.parent.tabs;
      }
      return [];
    },
    activeTab(): number {
      if (this.parent && this.parent.activeTab) {
        return this.parent.activeTab;
      }
      return 0;
    },
    slots(): VNode[] {
      if (!this.$slots || !this.$slots.default) return [];
      return this.$slots.default();
    },
  },
  methods: {
    isTabItem(slot: VNode): boolean {
      return slot.type.name === 'TabItem';
    },
    isTabActive(slotTab: string) {
      return slotTab === this.tabs[this.activeTab].key;
    },
  },
  render() {
    return [
      h('div', { class: 'tabs-body' }, [
        this.slots.filter(this.isTabItem)
          .map((slot: VNode) => {
            if (this.isTabActive(slot.props.tab)) {
              return h('div', { }, slot.children);
            }
            return null;
          }),
      ]),
    ];
  },
});
</script>

<style lang="stylus">
.tabs-body
  background: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  margin-left: var(--layout-spacing-unit)
  width: 70%
</style>
