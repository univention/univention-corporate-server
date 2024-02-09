<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <slot
    :active-tab="activeTab"
    :on-active-tab="parent.onActiveTab"
  >
    <div
      class="tabs-header"
      role="tablist"
    >
      <div
        v-for="(tab, index) in tabs"
        :key="index"
        class="tabs-header__item"
        :class="{ 'tabs-header__item--active': index === activeTab }"
        role="presentation"
        @click="parent.onActiveTab(index)"
      >
        {{ tab.label }}
      </div>
    </div>
  </slot>
</template>

<script lang="ts">
import type { Tab } from 'components/widgets/Tabs/types';
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'TabsHeader',
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
  },
});
</script>

<style lang="stylus">
.tabs-header
  background: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  padding: 20px
  width: 30%
  margin-right: var(--layout-spacing-unit)

  &__item
    font-size: var(--font-size-3)
    color: var(--font-color-contrast-middle)
    cursor: pointer

    &:hover
      text-decoration: underline

    &--active
      color: var(--font-color-contrast-high)
      text-decoration: underline
</style>
