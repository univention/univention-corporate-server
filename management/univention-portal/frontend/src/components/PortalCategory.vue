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
  <div
    :class="{'portal-category--empty': (!editMode && !hasTiles), 'portal-category--dragging': isBeingDragged }"
    class="portal-category"
    @drop="dropped"
    @dragover.prevent
    @dragenter.prevent
  >
    <h2
      v-if="editMode || showCategoryHeadline || hasTiles"
      class="portal-category__title"
      :class="{'portal-category__title-virtual': virtual }"
    >
      <icon-button
        v-if="editMode && !virtual && !isTouchDevice"
        icon="move"
        class="portal-category__edit-button icon-button--admin"
        :aria-label-prop="MOVE_CATEGORY"
        @click="enterMoveMode"
        @keydown.esc="cancelMoveMode"
        @keydown.up.prevent="moveUp"
        @keydown.down.prevent="moveDown"
      />
      <icon-button
        v-if="editMode && !virtual"
        icon="edit-2"
        class="portal-category__edit-button icon-button--admin"
        :aria-label-prop="EDIT_CATEGORY"
        @click="editCategory"
      />
      <span
        :draggable="editMode && !virtual"
        @dragstart="dragstart"
        @dragenter="dragenter"
        @dragend="dragend"
      >
        {{ $localized(title) }}
      </span>
    </h2>
    <div
      class="portal-category__tiles"
    >
      <template
        v-for="tile in tiles"
        :key="tile.id"
      >
        <div
          v-if="tileMatchesQuery(tile)"
        >
          <portal-folder
            v-if="tile.isFolder"
            :id="tile.id"
            :dn="tile.dn"
            :super-dn="dn"
            :title="tile.title"
            :tiles="tile.tiles"
          />
          <portal-tile
            v-else
            :id="tile.id"
            :dn="tile.dn"
            :super-dn="dn"
            :title="tile.title"
            :description="tile.description"
            :activated="tile.activated"
            :anonymous="tile.anonymous"
            :background-color="tile.backgroundColor"
            :links="tile.links"
            :allowed-groups="tile.allowedGroups"
            :link-target="tile.linkTarget"
            :original-link-target="tile.originalLinkTarget"
            :path-to-logo="tile.pathToLogo"
          />
        </div>
      </template>
      <tile-add
        v-if="editMode"
        :super-dn="dn"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import TileAdd from '@/components/admin/TileAdd.vue';
import IconButton from '@/components/globals/IconButton.vue';
import PortalFolder from '@/components/PortalFolder.vue';
import PortalTile from '@/components/PortalTile.vue';
import Draggable from '@/mixins/Draggable.vue';
import {
  Title,
  Tile,
  FolderTile,
  Description,
  BaseTile,
} from '@/store/modules/portalData/portalData.models';

interface PortalCategoryData {
  showCategoryHeadline: boolean,
}

export default defineComponent({
  name: 'PortalCategory',
  components: {
    TileAdd,
    PortalTile,
    PortalFolder,
    IconButton,
  },
  mixins: [
    Draggable,
  ],
  props: {
    dn: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<Title>,
      required: true,
    },
    virtual: {
      type: Boolean,
      required: true,
    },
    tiles: {
      type: Array as PropType<Tile[]>,
      required: true,
    },
  },
  data(): PortalCategoryData {
    return {
      showCategoryHeadline: false,
    };
  },
  computed: {
    ...mapGetters({
      editMode: 'portalData/editMode',
      searchQuery: 'search/searchQuery',
      dragDropIds: 'dragndrop/getId',
      inDragnDropMode: 'dragndrop/inDragnDropMode',
      portalContent: 'portalData/portalContent',
    }),
    isTouchDevice(): boolean {
      return 'ontouchstart' in document.documentElement;
    },
    hasTiles(): boolean {
      return this.tiles.some((tile) => this.tileMatchesQuery(tile));
    },
    MOVE_CATEGORY(): string {
      return _('Move category');
    },
    EDIT_CATEGORY(): string {
      return _('Edit category');
    },
  },
  methods: {
    async dropped(evt: DragEvent) {
      evt.preventDefault();
      if (evt.dataTransfer === null) {
        return;
      }
      const data = this.dragDropIds;
      if (this.dn === data.superDn) {
        this.$store.dispatch('dragndrop/dropped');
        this.$store.dispatch('activateLoadingState');
        await this.$store.dispatch('portalData/saveContent');
        this.$store.dispatch('deactivateLoadingState');
      } else if (!data.superDn) {
        this.$store.dispatch('dragndrop/dropped');
        this.$store.dispatch('activateLoadingState');
        await this.$store.dispatch('portalData/savePortalCategories');
        this.$store.dispatch('deactivateLoadingState');
      }
    },
    cancelMoveMode() {
      this.$store.dispatch('dragndrop/revert');
      this.$store.dispatch('dragndrop/dropped');
    },
    async enterMoveMode() {
      if (this.isBeingDragged) {
        this.$store.dispatch('dragndrop/dropped');
        this.$store.dispatch('activateLoadingState');
        await this.$store.dispatch('portalData/savePortalCategories');
        this.$store.dispatch('deactivateLoadingState');
      } else {
        // @ts-ignore
        this.dragstart();
      }
    },
    moveUp(evt) {
      if (!this.isBeingDragged) {
        return;
      }
      const otherId = this.dn;
      const otherIdx = this.portalContent.findIndex(([categoryDn]) => categoryDn === otherId);
      const myIdx = otherIdx - 1;
      const myId = this.portalContent[myIdx]?.[0];
      if (!myId || myId === '$$menu$$' || myId === '$$user$$') {
        return;
      }
      this.$store.dispatch('portalData/reshuffleContent', {
        src: otherId,
        dst: myId,
      });
      this.$nextTick(() => {
        evt.target.focus();
      });
      this.$store.dispatch('activity/addMessage', {
        id: 'dnd',
        msg: _('Categories "%(cat1)s" and "%(cat2)s" changed places', {
          cat1: this.$localized(this.title),
          cat2: this.$localized(this.title),
        }),
      });
    },
    moveDown(evt) {
      if (!this.isBeingDragged) {
        return;
      }
      const otherId = this.dn;
      const otherIdx = this.portalContent.findIndex(([categoryDn]) => categoryDn === otherId);
      const myIdx = otherIdx + 1;
      const myId = this.portalContent[myIdx]?.[0];
      if (!myId) {
        return;
      }
      this.$store.dispatch('portalData/reshuffleContent', {
        src: otherId,
        dst: myId,
      });
      this.$nextTick(() => {
        evt.target.focus();
      });
      this.$store.dispatch('activity/addMessage', {
        id: 'dnd',
        msg: _('Categories "%(cat1)s" and "%(cat2)s" changed places', {
          cat1: this.$localized(this.title),
          cat2: this.$localized(this.title),
        }),
      });
    },
    editCategory() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'AdminCategory',
        stubborn: true,
        props: {
          modelValue: this.$props,
          label: 'Edit category',
        },
      });
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

<style lang="stylus">
.portal-category
  margin-bottom: calc(8 * var(--layout-spacing-unit));

  &--empty
    margin-bottom: 0

  &--dragging
    transform: rotate(-1deg)

  &__tiles
    display: grid
    grid-template-columns: repeat(auto-fill, var(--app-tile-side-length))
    grid-gap: calc(6 * var(--layout-spacing-unit))

    &--editmode
      display: block

  &__edit-button
    padding 0

  &__title
    height: var(--button-size)
    display: inline-flex
    align-items: center
    margin-top: 0
    margin-bottom: calc(3 * var(--layout-spacing-unit))

    & [draggable="true"]
      cursor: move
  &__title-virtual
    font-style: italic
</style>
