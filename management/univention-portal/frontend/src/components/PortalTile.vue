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
    <component
      :is="wrapperTag"
      :href="link"
      :target="anchorTarget"
      :aria-describedby="createID()"
      class="portal-tile"
      data-test="tileLink"
      @mouseover="editMode || showTooltip()"
      @mouseleave="hideTooltip"
      @mousedown="hideTooltip"
      @click="tileClick"
      @keydown.tab.exact="setFocus($event, 'forward')"
      @keydown.shift.tab.exact="setFocus($event, 'backward')"
      @focus="showTooltip()"
      @blur="hideTooltip()"
    >
      <div
        :style="`background: ${backgroundColor || 'var(--color-grey40)'}`"
        :class="[
          'portal-tile__box', { 'portal-tile__box--dragable': editMode }
        ]"
      >
        <img
          :src="pathToLogo || './questionMark.svg'"
          onerror="this.src='./questionMark.svg'"
          :alt="`Logo ${$localized(title)}`"
          class="portal-tile__img"
        >
      </div>
      <span
        class="portal-tile__name"
        @click.prevent="tileClick"
      >
        {{ $localized(title) }}
      </span>

      <header-button
        v-if="!noEdit && isAdmin"
        :icon="buttonIcon"
        :aria-label="ariaLabelButton"
        :no-click="true"
        class="portal-tile__edit-button"
        @click.prevent="editTile()"
      />
    </component>
    <portal-tool-tip
      :title="$localized(title)"
      :icon="pathToLogo"
      :description="$localized(description)"
      :aria-id="createID()"
      :is-displayed="isActive"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

import PortalToolTip from '@/components/PortalToolTip.vue';
import TileClick from '@/mixins/TileClick.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';

import { Title, Description } from '@/store/models';

interface PortalTileData {
  isActive: boolean,
}

export default defineComponent({
  name: 'PortalTile',
  components: {
    PortalToolTip,
    HeaderButton,
  },
  mixins: [
    TileClick,
  ],
  props: {
    title: {
      type: Object as PropType<Title>,
      required: true,
    },
    description: {
      type: Object as PropType<Description>,
      required: true,
    },
    pathToLogo: {
      type: String,
      required: false,
      default: 'questionMark.svg',
    },
    backgroundColor: {
      type: String,
      default: 'var(--color-grey40)',
    },
    inFolder: {
      type: Boolean,
      default: false,
    },
    hasFocus: {
      type: Boolean,
      default: false,
    },
    lastElement: {
      type: Boolean,
      default: false,
    },
    firstElement: {
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
  emits: ['keepFocusInFolderModal'],
  data(): PortalTileData {
    return {
      isActive: false,
    };
  },
  computed: {
    wrapperTag(): string {
      return (this.inFolder || this.editMode) ? 'div' : 'a';
    },
  },
  mounted() {
    if (this.hasFocus) {
      this.$el.children[0].focus(); // sets focus to first Element in opened Folder
    }
  },
  methods: {
    hideTooltip(): void {
      this.isActive = false;
    },
    showTooltip(): void {
      if (!this.inFolder) {
        this.isActive = true;
      }
    },
    setFocus(event, direction): void {
      if (this.lastElement && direction === 'forward') {
        event.preventDefault();
        this.$emit('keepFocusInFolderModal', 'focusFirst');
      } else if (this.firstElement && direction === 'backward') {
        event.preventDefault();
        this.$emit('keepFocusInFolderModal', 'focusLast');
      }
    },
    editTile() {
      console.log('editTile');
    },
    showToolTipIfFocused() {
      if (this.isActive) {
        this.hideTooltip();
      } else {
        this.showTooltip();
      }
    },
    createID() {
      return `element-${this.$.uid}`;
    },
  },
});
</script>

<style lang="stylus">
.portal-tile
  position: relative
  outline: 0
  width: var(--app-tile-side-length)
  display: flex
  flex-direction: column
  align-items: center
  cursor: pointer
  color: var(--font-color-contrast-high)
  text-decoration: none

  &:hover
    color: var(--font-color-contrast-high)
    text-decoration: none

  &__box
    border-radius: 15%
    display: flex
    align-items: center
    justify-content: center
    box-shadow: var(--box-shadow)
    background: var(--color-grey40)
    width: var(--app-tile-side-length)
    height: @width
    margin-bottom: calc(2 * var(--layout-spacing-unit))
    border: 0.2rem solid transparent

    ~/:focus &
      border-color: var(--color-primary)

    &--dragable
      position: relative

      &:after
        content: ' ';
        position: absolute;
        top: 0;
        right: 0;
        bottom: 0;
        left: 0;
        z-index: $zindex-1;

  &__img
    width: 80%

  &__name
    text-align: center
    width: 100%
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap

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

    &--in-modal
      position relative

// current fix for edit button in modal
.portal-folder__in-modal
  & .portal-tile__edit-button
    display: none
</style>
