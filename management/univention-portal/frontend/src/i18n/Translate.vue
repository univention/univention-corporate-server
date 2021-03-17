<template>
  <span>{{ translated }}</span>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import { catalog } from '@/assets/data/dictionary';

export default defineComponent({
  name: 'Translate',
  props: {
    i18nKey: {
      type: String,
      required: true,
      validator(i18nKey: string) {
        return i18nKey in catalog;
      },
    },
  },
  computed: {
    translated(): string {
      return catalog[this.i18nKey].translated.value;
    },
  },
});
</script>
