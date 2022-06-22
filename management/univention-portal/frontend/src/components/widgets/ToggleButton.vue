<template>
  <icon-button
    :icon="isToggled ? toggleIcons.toggled : toggleIcons.initial"
    :aria-label-prop="toggleLabel"
    :title="toggleLabel"
    :active-at="activeAt"
    class="toggle-button"
    data-test="toggle-button"
    @click="$emit('update:isToggled', !isToggled)"
  />
</template>
<script lang="ts">
import { defineComponent, PropType } from 'vue';

import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'ToggleButton',
  components: {
    IconButton,
  },
  props: {
    isToggled: {
      type: Boolean,
      required: true,
    },
    toggleLabels: {
      type: Object as PropType<Record<string, string>>,
      required: true,
    },
    toggleIcons: {
      type: Object as PropType<Record<string, string>>,
      required: true,
    },
    activeAt: {
      type: Array,
      default: () => ['portal'],
    },
  },
  emits: ['update:isToggled'],
  computed: {
    toggleLabel(): string {
      return this.isToggled ? this.toggleLabels.toggled : this.toggleLabels.initial;
    },
  },
});

</script>
