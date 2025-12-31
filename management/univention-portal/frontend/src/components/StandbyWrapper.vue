<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    class="standbyWrapper"
  >
    <standby-circle />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import StandbyCircle from '@/components/StandbyCircle.vue';

export default defineComponent({
  name: 'StandyWrapper',
  components: {
    StandbyCircle,
  },
});
</script>

<style lang="stylus">
.standbyWrapper
  width: 100%
  height: 100%
  display: flex
  align-items: center
  justify-content: center
</style>
