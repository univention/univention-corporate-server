<template>
  <div
    ref="draggable"
    draggable="true"
    :class="!isDragging || dragClass"
    @dragover.prevent="itemDragOver"
    @dragstart="itemDragStart"
    @dragend="itemDragEnd"
    @dragleave.prevent
  >
    <slot />
  </div>
</template>

<script>
import { toRefs } from 'vue';
import { useDraggableItem } from '@/jsHelper/draggable';

export default {
  name: 'DraggableItem',
  props: {
    item: {
      type: Object,
      default: () => ({}),
    },
    position: {
      type: Number,
      default: 0,
    },
    dropZoneId: {
      type: Number,
      default: -1,
    },
    dragClass: {
      type: String,
      default: 'draggable-item__dragging',
    },
  },
  setup(props, context) {
    const { item, position, dropZoneId } = toRefs(props);
    const {
      draggable,
      isDragging,
      itemDragStart,
      itemDragOver,
      itemDragEnd,
      transitionStart,
      transitionEnd,
    } = useDraggableItem({ item, position, dropZoneId }, context);

    return {
      draggable,
      isDragging,
      itemDragStart,
      itemDragOver,
      itemDragEnd,
      transitionStart,
      transitionEnd,
    };
  },
};
</script>

<style lang="stylus">
.draggable-item
  &__dragging
    opacity: 0.2
</style>
