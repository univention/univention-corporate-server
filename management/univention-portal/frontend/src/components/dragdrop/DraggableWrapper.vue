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
  <div>
    <template
      v-for="(item, index) in defaultItems"
      :key="index"
      name="draggable-wrapper"
    >
      <draggable-item
        :id="item.id"
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
    </template>

    <tile-add
      :super-dn="categoryDn"
    />
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
    categoryDn: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Array,
      default: () => [],
    },
    dropZoneId: {
      type: Number,
      default: -1,
    },
  },
  setup(props, context) {
    const { modelValue, dropZoneId, categoryDn } = toRefs(props);

    const {
      defaultItems,
      onItemDragOver,
    } = useDraggableContainer(
      {
        initialItems: modelValue,
        dropZoneId,
        categoryDn,
      },
      context,
    );

    return {
      defaultItems,
      onItemDragOver,
    };
  },
});
</script>
