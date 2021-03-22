<!--
Copyright 2021 Univention GmbH

https://www.univention.de/

All rights reserved.

The source code of this program is made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use this program under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/>.
-->
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

<script lang="ts">
import { toRefs, defineComponent, ComputedRef, computed } from 'vue';
import DraggableItem from '@/components/dragdrop/DraggableItem.vue';
import TileAdd from '@/components/admin/TileAdd.vue';
import { useDraggableContainer } from '@/jsHelper/draggable';

export default defineComponent({
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
    const { modelValue, dropZoneId, transition } = toRefs(props);

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

    const transitionStyle: ComputedRef<string> = computed((): string => `transform ${transition}ms`);

    return {
      defaultItems,
      onItemDragOver,
      containerDragOver,
      placeholder,
      transitionStyle,
    };
  },
});
</script>

<style lang="stylus" scoped>
// class name follows https://v3.vuejs.org/guide/transitions-list.html#list-move-transitions
.draggable-wrapper-move
  transition: v-bind(transitionStyle)
</style>
