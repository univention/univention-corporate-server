<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <slot />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'TabItem',
  props: {
    tab: {
      type: String,
      required: true,
    },
  },
});
</script>
