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
    v-if="hasTiles || editMode"
    class="portal-folder"
    :draggable="editMode && !inModal"
    :class="[
      { 'portal-folder__in-modal': inModal },
    ]"
    @dragstart="dragstart"
    @dragenter="dragenter"
    @dragend="dragend"
  >
    <button
      class="portal-tile__box"
      tabindex="0"
      :aria-label="ariaLabelFolder"
      @click="openFolder"
      @keypress.enter="openFolder"
      @keyup.esc.stop="closeFolder()"
    >
      <div
        class="portal-folder__thumbnails"
        :class="{ 'portal-folder__thumbnails--in-modal': inModal }"
      >
        <div
          v-for="(tile, index) in tiles"
          :key="index"
        >
          <portal-tile
            :ref="'portalFolderChildren' + index"
            v-bind="tile"
            :minified="!inModal"
            :has-focus="setFocus(index)"
            :last-element="isLastElement(index, tiles)"
            :first-element="isFirstElement(index)"
            :from-folder="true"
            :super-dn="dn"
            @keepFocusInFolderModal="keepFocusInFolderModal"
          />
        </div>
        <div
          v-if="editMode && inModal"
        >
          <div class="portal-tile__root-element">
            <tile-add
              :for-folder="true"
              :super-dn="dn"
            />
          </div>
        </div>
      </div>
    </button>
    <span
      class="portal-folder__name"
      @click="openFolder"
    >
      {{ $localized(title) }}
    </span>
    <icon-button
      v-if="editMode && !inModal"
      icon="edit-2"
      class="portal-folder__edit-button"
      @click="editFolder()"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';

import PortalTile from '@/components/PortalTile.vue';
import Draggable from '@/mixins/Draggable.vue';
import IconButton from '@/components/globals/IconButton.vue';
import TileAdd from '@/components/admin/TileAdd.vue';
import { Title, Tile } from '@/store/modules/portalData/portalData.models';

export default defineComponent({
  name: 'PortalFolder',
  components: {
    PortalTile,
    IconButton,
    TileAdd,
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
    tiles: {
      type: Array as PropType<Tile[]>,
      required: true,
    },
    superDn: {
      type: String,
      required: true,
    },
    inModal: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    ...mapGetters({ editMode: 'portalData/editMode' }),
    hasTiles(): boolean {
      return this.tiles.length > 0;
    },
    ariaLabelFolder(): string {
      return `${this.$translateLabel('FOLDER')}`;
    },
  },
  methods: {
    closeFolder(): void {
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('tooltip/unsetTooltip');
    },
    openFolder() {
      if (this.inModal) {
        return;
      }
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'PortalFolder',
        props: { ...this.$props, inModal: true },
      });
    },
    setFocus(index): boolean {
      return this.inModal && index === 0;
    },
    isLastElement(index, array): boolean {
      return index === (array.length - 1);
    },
    isFirstElement(index): boolean {
      return index === 0;
    },
    keepFocusInFolderModal(focusElement) {
      // TODO: Following $refs are bad practice and do not have proper typescript support
      const firstElement = (this.$refs.portalFolderChildren0 as HTMLFormElement).$el.children[0];
      const lastChild = `portalFolderChildren${this.tiles.length - 1}`;
      const lastElement = (this.$refs[lastChild] as HTMLFormElement).$el.children[0];

      if (focusElement === 'focusLast') {
        lastElement.focus();
      } else if (focusElement === 'focusFirst') {
        firstElement.focus();
      }
    },
    editFolder() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'AdminFolder',
        props: {
          modelValue: this.$props,
          superDn: this.superDn,
          label: 'EDIT_FOLDER',
        },
      });
    },
  },
});
</script>

<style lang="stylus">
.portal-folder
  position: relative
  width: var(--app-tile-side-length)
  display: flex
  flex-direction: column
  align-items: center
  cursor: pointer

  &__name
    text-align: center
    width: 100%
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap
    text-shadow: 0 0.1rem 0.1rem rgba(0, 0, 0, 0.3)

  &__in-modal
    cursor: default

    button
      text-transform: none
      cursor: default

    .portal-folder__name
      margin-top: calc(3 * var(--layout-spacing-unit))
      font-size: var(--font-size-1)
      width: unset

    > .portal-tile
      &__box
        width: calc(5 * var(--app-tile-side-length))
        height: @width
        max-width: 100vw
        margin-bottom: 0

        .portal-tile
          cursor: pointer
          width: var(--app-tile-side-length)
          &__box
            width: var(--app-tile-side-length)
            height: @width
    &__box
      width: var(--app-tile-side-length)
      height: var(--app-tile-side-length)

    .portal-folder__thumbnails .portal-tile__name
        display: block;

  &__thumbnails
    width: 100%
    height: 100%
    display: flex
    flex-wrap: wrap;
    justify-content: flex-start;
    align-content: flex-start;
    padding: 0.3rem;
    box-sizing: border-box;
    overflow: hidden
    > div
      height: min-content
      width: var(--portal-folder-tile-width)
      max-width: 50%
      margin-bottom: 0;

    &--in-modal
      max-height: 100vh
      overflow: auto
      box-sizing: border-box;
      padding:  var(--portal-folder-padding)
      padding-bottom: 0

      > div
        margin-bottom: 3rem
    .portal-tile
      width: calc(0.25 * var(--app-tile-side-length))
      &__box
        width: calc(0.25 * var(--app-tile-side-length))
        height: @width
        margin-bottom: var(--layout-spacing-unit)
        padding:  calc(var(--layout-spacing-unit))

      &__name
        display: none;

  &__edit-button
    position: absolute
    background-color: var(--color-grey0)
    top: -0.75em
    right: -0.75em
    z-index: $zindex-1

    @extend .icon-button--admin

  .portal-tile__box
    background-color: var(--color-grey0)
    padding: 0

&:focus
  border-color: var(--color-focus)
  outline: none;
</style>
