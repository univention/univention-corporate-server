<template>
  <pre class="draggable-debugger">
    {{ JSON.stringify(items, undefined, 4) }}
  </pre>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'DraggableDebugger',
  props: {
    items: {
      type: Object,
      default: () => ({}),
    },
  },
});
</script>

<style lang="stylus" scoped>
.draggable-debugger
  background-color: #ccc
  margin: 30px
  padding: 10px
  width: 100%
  min-height: 200px
  color: #000
</style>
