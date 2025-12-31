<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <component
    :is="tag"
    :id="id"
    :tabindex="tabIndex"
    @focus="saveFocus"
  >
    <slot />
  </component>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'TabindexElement',
  props: {
    id: {
      type: String,
      required: true,
    },
    tag: {
      type: String,
      required: true,
    },
    activeAt: {
      type: Array,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      activityLevel: 'activity/level',
    }),
    tabIndex(): number {
      if (this.activeAt.indexOf(this.activityLevel) > -1) {
        return 0;
      }
      return -1;
    },
  },
  methods: {
    saveFocus(): void {
      this.$store.dispatch('activity/saveFocus', {
        id: this.id,
      });
    },
  },
});
</script>
