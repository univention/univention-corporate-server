<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    class="sr-only sr-only-mobile"
  >
    <span
      aria-live="assertive"
      aria-relevant="additions removals"
      aria-atomic="true"
    >
      {{ message }}
    </span>
  </div>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'ScreenReaderAnnouncer',
  props: {
  },
  computed: {
    ...mapGetters({
      message: 'activity/message',
    }),
  },
});
</script>
