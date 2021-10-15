<template>
  <div>
    {{ toolTipText }}
  </div>
</template>
<script>
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'CursorToolTip',
  props: {
    toolTipText: {
      type: string,
      required: true,
    },
  },
});
</script>
<style>
</style>
