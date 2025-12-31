<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <span
    class="read-only-field"
    :tabindex="tabindex"
  >{{ label }}</span>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'ReadOnlyField',
  props: {
    label: {
      type: String,
      required: true,
    },
    tabindex: {
      type: Number,
      required: true,
    },
  },
});
</script>
<style  lang="stylus">
.read-only-field
  display: block
  color: var(--font-color-contrast-high)
  border: 2px solid transparent
  font-size: var(--font-size-3);
  &:focus
    border-color: var(--font-color-contrast-high)
    outline: 0
</style>
