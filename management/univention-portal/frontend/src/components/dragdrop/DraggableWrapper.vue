<template>
  <div @dragover.prevent="containerDragOver">
    <transition-group
      v-for="(item, index) in defaultItems"
      :key="index"
      name="draggable-wrapper"
    >
      <draggable-item
        :id="item.id"
        :key="item.id"
        :item="item"
        :drop-zone-id="dropZoneId"
        :position="index"
        @itemDragOver="onItemDragOver"
      >
        <slot
          name="item"
          :item="item"
        />
      </draggable-item>
      <div
        v-if="placeholder"
        :id="`placeholder-${item.id}`"
        class="dragdrop__placeholder--dotted"
      />
    </transition-group>

    <tile-add />
  </div>
</template>

<script>
import { toRefs } from 'vue';
import DraggableItem from '@/components/dragdrop/DraggableItem.vue';
import TileAdd from '@/components/edit/TileAdd.vue';
import { useDraggableContainer } from '@/jsHelper/draggable';

export default {
  name: 'DraggableWrapper',
  components: {
    DraggableItem,
    TileAdd,
  },
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
    dropZoneId: {
      type: Number,
      default: -1,
    },
    transition: {
      default: '0',
      type: String,
    },
  },
  setup(props, context) {
    const { modelValue, dropZoneId } = toRefs(props);

    const {
      defaultItems,
      onItemDragOver,
      containerDragOver,
    } = useDraggableContainer(
      {
        initialItems: modelValue,
        dropZoneId,
      },
      context,
    );

    const placeholder = false;

    return {
      defaultItems,
      onItemDragOver,
      containerDragOver,
      placeholder,
    };
  },
  computed: {
    transitionStyle() {
      return `transform ${this.transition}ms`;
    },
  },
};
</script>

<style lang="stylus" scoped>
// class name follows https://v3.vuejs.org/guide/transitions-list.html#list-move-transitions
.draggable-wrapper-move
  transition: v-bind(transitionStyle)
</style>
