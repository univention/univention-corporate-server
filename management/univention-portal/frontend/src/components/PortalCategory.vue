<!--
  // Copyright 2021 Univention GmbH

  // https://www.univention.de/

  // All rights reserved.

  // The source code of this program is made available
  // under the terms of the GNU Affero General Public License version 3
  // (GNU AGPL V3) as published by the Free Software Foundation.

  // Binary versions of this program provided by Univention to you as
  // well as other copyrighted, protected or trademarked materials like
  // Logos, graphics, fonts, specific documentations and configurations,
  // cryptographic keys etc. are subject to a license agreement between
  // you and Univention and not subject to the GNU AGPL V3.

  // In the case you use this program under the terms of the GNU AGPL V3,
  // the program is provided in the hope that it will be useful,
  // but WITHOUT ANY WARRANTY; without even the implied warranty of
  // MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  // GNU Affero General Public License for more details.

  // You should have received a copy of the GNU Affero General Public
  // License with the Debian GNU/Linux or Univention distribution in file
  // /usr/share/common-licenses/AGPL-3; if not, see
  // <https://www.gnu.org/licenses/>.
-->
<template>
  <div
    :class="{'portal-category--empty': (!editMode && !hasTiles) }"
    class="portal-category"
  >
    <h2
      v-if="editMode || showCategoryHeadline || hasTiles"
      :class="!editMode || 'portal-category__title--edit'"
      class="portal-category__title"
      @click.prevent="editMode ? editCategory() : ''"
    >
      <header-button
        v-if="editMode"
        icon="edit-2"
        :aria-label="ariaLabelButton"
        :no-click="true"
        class="portal-category__edit-button"
      />{{ $localized(title) }}
    </h2>
    <div
      class="portal-category__tiles dragdrop__container"
      :class="{'portal-category__tiles--editmode': editMode}"
    >
      <template
        v-if="editMode"
      >
        <draggable-wrapper
          v-model="vTiles"
          :category-dn="dn"
          :drop-zone-id="dropZone"
          :data-drop-zone-id="dropZone"
          class="dragdrop__drop-zone"
        >
          <template #item="{ item }">
            <div
              v-if="tileMatchesQuery(item)"
              :key="item.id"
              class="dragdrop__draggable-item"
            >
              <portal-folder
                v-if="item.isFolder"
                v-bind="item"
                :category-dn="dn"
              />
              <portal-tile
                v-else
                v-bind="item"
                :category-dn="dn"
              />
            </div>
          </template>
        </draggable-wrapper>
      </template>

      <template v-else>
        <template
          v-for="tile in tiles"
        >
          <div
            v-if="tileMatchesQuery(tile)"
            :key="tile.id"
          >
            <portal-folder
              v-if="tile.isFolder"
              v-bind="tile"
              :category-dn="dn"
            />
            <portal-tile
              v-else
              v-bind="tile"
              :category-dn="dn"
            />
          </div>
        </template>
      </template>
    </div>

    <draggable-debugger
      v-if="editMode && debug"
      :items="vTiles"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';
import { put } from '@/jsHelper/admin';

import DraggableWrapper from '@/components/dragdrop/DraggableWrapper.vue';
import DraggableDebugger from '@/components/dragdrop/DraggableDebugger.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';
import PortalFolder from '@/components/PortalFolder.vue';
import PortalTile from '@/components/PortalTile.vue';
import {
  Title,
  Tile,
  FolderTile,
  Description,
  BaseTile,
} from '@/store/modules/portalData/portalData.models';

function isEqual(arr1, arr2) {
  if (arr1.length !== arr2.length) {
    return false;
  }
  return arr1.every((v, i) => v === arr2[i]);
}

interface PortalCategoryData {
  vTiles: Tile[],
  debug: boolean,
  showCategoryHeadline: boolean,
  categoryModal: boolean,
}

export default defineComponent({
  name: 'PortalCategory',
  components: {
    PortalTile,
    PortalFolder,
    HeaderButton,
    DraggableWrapper,
    DraggableDebugger,
  },
  props: {
    dn: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<Title>,
      required: true,
    },
    tiles: {
      type: Array as PropType<Tile[]>,
      required: true,
    },
    dropZone: {
      type: Number,
      required: true,
    },
    ariaLabelButton: {
      type: String,
      default: 'Tab Aria Label',
    },
  },
  data(): PortalCategoryData {
    return {
      vTiles: [],
      debug: false, // `true` enables the debugger for the tiles array(s) in admin mode
      categoryModal: false,
      showCategoryHeadline: false,
    };
  },
  computed: {
    ...mapGetters({
      editMode: 'portalData/editMode',
      searchQuery: 'search/searchQuery',
    }),
    hasTiles(): boolean {
      return this.tiles.some((tile) => this.tileMatchesQuery(tile));
    },
  },
  watch: {
    async vTiles(val) {
      if (!this.editMode) {
        return;
      }
      const oldEntries = this.tiles.map((tile) => tile.dn);
      const entries = val.map((tile) => tile.dn);
      if (isEqual(oldEntries, entries)) {
        return;
      }
      this.$store.dispatch('activateLoadingState');
      const dn = this.dn;
      const attrs = {
        entries,
      };
      console.info('Rearranging entries for', dn);
      await put(dn, attrs, this.$store, 'ENTRY_ORDER_SUCCESS', 'ENTRY_ORDER_FAILURE');
      this.$store.dispatch('deactivateLoadingState');
    },
  },
  created(): void {
    this.vTiles = [...this.tiles];
  },
  methods: {
    editCategory() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'AdminCategory',
        props: {
          modelValue: this.$props,
          label: 'EDIT_CATEGORY',
        },
      });
    },
    closeModal() {
      this.categoryModal = false;
    },
    removeCategory() {
      console.log('remove category');
      this.closeModal();
    },
    saveCategory(value) {
      // save the changes
      console.log('save category: ', value);

      this.closeModal();
    },
    titleMatchesQuery(title: Title): boolean {
      return this.$localized(title).toLowerCase()
        .includes(this.searchQuery.toLowerCase());
    },
    descriptionMatchesQuery(description: Description): boolean {
      return this.$localized(description).toLowerCase()
        .includes(this.searchQuery.toLowerCase());
    },
    tileMatchesQuery(tile: Tile): boolean {
      const titleMatch = this.titleMatchesQuery(tile.title);
      const descriptionMatch = (tile as BaseTile).description ? this.descriptionMatchesQuery((tile as BaseTile).description as Description) : false;
      const folderMatch = tile.isFolder && (tile as FolderTile).tiles.some((t) => this.titleMatchesQuery(t.title));
      return titleMatch || folderMatch || descriptionMatch;
    },
  },
});
</script>

<style lang="stylus" scoped>
.portal-category
  margin-bottom: calc(10 * var(--layout-spacing-unit));

  &--empty {
    margin-bottom: 0;
  }

  &__tiles
    display: grid
    grid-template-columns: repeat(auto-fill, var(--app-tile-side-length))
    grid-gap: calc(6 * var(--layout-spacing-unit))

    &--editmode {
      display: block
    }

  &__drop-zone
    width: 100%;
    overflow: hidden;
    &--hidden
      display: none

  &__drag-element
    height: 210px
    width: 160px

  &__tile-dotted
    width: calc(20 * var(--layout-spacing-unit))
    height: calc(20 * var(--layout-spacing-unit))
    border-radius: 15%
    border: 3px dashed var(--color-grey40) !important

  &__edit-button
    @extend .icon-button--admin

  &__title
    height: var(--button-size)
    display: inline-flex
    align-items: center
    margin-top: 0
    margin-bottom: calc(6 * var(--layout-spacing-unit))

    &--edit
      cursor: pointer
</style>
