<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div class="tabs">
    <slot />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import type { Tab } from './types';

interface Data {
  activeTab: number;
}

export default defineComponent({
  name: 'Tab',
  props: {
    tabs: {
      type: Array as () => Tab[],
      required: true,
    },
  },
  data(): Data {
    return {
      activeTab: 0,
    };
  },
  methods: {
    onActiveTab(tab: number | string): void {
      if (typeof tab === 'string') {
        this.activeTab = this.tabs.findIndex((t) => t.key === tab);
      } else {
        if (tab < 0 || tab > this.tabs.length - 1) return;
        this.activeTab = tab;
      }
    },
  },
});
</script>

<style lang="stylus">
.tabs
  display: flex
</style>
