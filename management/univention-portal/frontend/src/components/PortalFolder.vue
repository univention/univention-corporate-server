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
    v-if="hasTiles"
    class="portal-folder"
    :class="{ 'portal-folder__in-modal': inModal }"
  >
    <button
      class="portal-tile__box"
      tabindex="0"
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
            :in-folder="!inModal"
            :has-focus="setFocus(index)"
            :last-element="isLastElement(index, tiles)"
            :first-element="isFirstElement(index)"
            :no-edit="true"
            @keepFocusInFolderModal="keepFocusInFolderModal"
            @clickAction="closeFolder"
          />
        </div>
      </div>
    </button>
    <span class="portal-folder__name">
      {{ $localized(title) }}
    </span>
    <header-button
      v-if="!noEdit && isAdmin && !inModal"
      :icon="buttonIcon"
      :aria-label="ariaLabelButton"
      :no-click="true"
      class="portal-folder__edit-button"
      @click.prevent="editFolder()"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

import PortalTile from '@/components/PortalTile.vue';
import PortalModal from '@/components/globals/PortalModal.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';
import { Title, Tile } from '@/store/models';

export default defineComponent({
  name: 'PortalFolder',
  components: {
    PortalTile,
    // TODO: Very strange behavior:
    // PortalModal component is not being used here,
    // but removing it moves the Sidebar to the middle
    // eslint-disable-next-line vue/no-unused-components
    PortalModal,
    HeaderButton,
  },
  props: {
    title: {
      type: Object as PropType<Title>,
      required: true,
    },
    tiles: {
      type: Array as PropType<Tile[]>,
      required: true,
    },
    inModal: {
      type: Boolean,
      default: false,
    },
    isAdmin: {
      type: Boolean,
      default: false,
    },
    noEdit: {
      type: Boolean,
      default: false,
    },
    buttonIcon: {
      type: String,
      default: 'edit-2',
    },
    ariaLabelButton: {
      type: String,
      default: 'Tab Aria Label',
    },
  },
  computed: {
    hasTiles(): boolean {
      return this.tiles.length > 0;
    },
  },
  methods: {
    closeFolder(): void {
      this.$store.dispatch('modal/setHideModal');
    },
    openFolder() {
      if (this.inModal) {
        return;
      }
      this.$store.dispatch('modal/setShowModal', {
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
    getLastElement() {
      console.log('ELEMENT');
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
      console.log('editFolder');
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
  border: 0.2rem solid transparent

  &__name
    text-align: center
    width: 100%
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap

  &__in-modal
    cursor: default

    button
      text-transform: none

    .portal-folder__name
      margin-top: calc(3 * var(--layout-spacing-unit))
      font-size: var(--font-size-1)

    > .portal-tile
      &__box
        width: calc(5 * var(--app-tile-side-length))
        height: @width
        max-width: 100vw
        margin-bottom: 0

        .portal-tile
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
    height:100%
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

      > div
        margin-bottom: 3rem
    .portal-tile
      width: calc(0.2 * var(--app-tile-side-length))
      &__box
        width: calc(0.2 * var(--app-tile-side-length))
        height: @width
        margin-bottom: var(--layout-spacing-unit)
        padding:  calc(var(--layout-spacing-unit))

      &__name
        display: none;

  &__edit-button
    user-select: none
    position: absolute
    top: -0.75em
    right: -0.75em
    width: 2em
    height: 2em
    background-color: var(--color-grey0)
    background-size: 1em
    background-repeat: no-repeat
    background-position: center
    border-radius: 50%
    box-shadow: var(--box-shadow)

  .portal-tile__box
    background: var(--color-grey0)
    padding: 0

&:focus
  border-color: var(--color-primary)
  outline: none;
</style>
