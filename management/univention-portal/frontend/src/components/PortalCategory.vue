<!--
  Copyright 2021-2022 Univention GmbH

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
    :class="{'portal-category--dragging': isBeingDragged}"
    class="portal-category"
    @drop="dropped"
    @dragover.prevent
    @dragenter.prevent
  >
    <h2
      class="portal-category__title"
      :class="{'portal-category__title-virtual': virtual}"
    >
      <icon-button
        v-if="editMode && !virtual && showEditButtonWhileDragging"
        icon="edit-2"
        class="portal-category__edit-button icon-button--admin"
        :aria-label-prop="EDIT_CATEGORY"
        @click="editCategory"
      />
      <icon-button
        v-if="editMode && !virtual && !isTouchDevice && showMoveButtonWhileDragging"
        :id="`${layoutId}-move-button`"
        icon="move"
        class="portal-category__edit-button icon-button--admin"
        :aria-label-prop="MOVE_CATEGORY"
        @click="dragKeyboardClick"
        @keydown.esc="dragend"
        @keydown.up="dragKeyboardDirection($event, 'up')"
        @keydown.down="dragKeyboardDirection($event, 'down')"
        @keydown.tab="handleTabWhileMoving"
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
        <portal-folder
          v-if="tile.isFolder"
          :id="tile.id"
          :layout-id="tile.layoutId"
          :dn="tile.dn"
          :super-dn="dn"
          :title="tile.title"
          :tiles="tile.tiles"
        />
        <portal-tile
          v-else
          :id="tile.id"
          :layout-id="tile.layoutId"
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
          :target="tile.target"
          :original-link-target="tile.originalLinkTarget"
          :path-to-logo="tile.pathToLogo"
        />
      </template>
      <tile-add
        v-if="editMode"
        :super-dn="dn"
        :super-layout-id="layoutId"
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
  Tile,
  LocalizedString,
} from '@/store/modules/portalData/portalData.models';

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
    layoutId: {
      type: String,
      required: true,
    },
    dn: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<LocalizedString>,
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
    categoryIndex: {
      type: Number,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      searchQuery: 'search/searchQuery',
    }),
    isTouchDevice(): boolean {
      return 'ontouchstart' in document.documentElement;
    },
    MOVE_CATEGORY(): string {
      return _('Move category: %(category)s', { category: this.$localized(this.title) });
    },
    EDIT_CATEGORY(): string {
      return _('Edit category: %(category)s', { category: this.$localized(this.title) });
    },
  },
  methods: {
    async dropped(evt: DragEvent) {
      evt.preventDefault();
      if (evt.dataTransfer === null) {
        return;
      }
      await this.$store.dispatch('portalData/saveLayout');
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
  },
});
</script>

<style lang="stylus">
.portal-category
  margin-bottom: calc(8 * var(--layout-spacing-unit));

  &--dragging
    .portal-tile__box,
    .tile-add__button
      transform: rotate(-10deg)
    .portal-tile--minified .portal-tile__box
      transform: none

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
