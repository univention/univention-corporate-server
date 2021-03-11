<template>
  <span>{{ translated }}</span>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';

import { catalog } from '@/i18n/translations';

@Options({
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
    translated() {
      return catalog[this.i18nKey].translated.value;
    },
  },
})

export default class Translate extends Vue {}
</script>
