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
  <div class="portal-tile__root-element">
    <tabindex-element
      :id="id"
      :tag="wrapperTag"
      :active-at="activeAt"
      :href="link"
      :target="anchorTarget"
      :aria-describedby="tileId"
      :aria-label="ariaLabelPortalTile"
      class="portal-tile"
      :draggable="editMode && !fromFolder"
      data-test="tileLink"
      @mouseenter="showTooltip()"
      @mouseleave="hideTooltip"
      @mousedown="hideTooltip"
      @focus="showTooltip()"
      @focusin="setAriaDescribedBy"
      @focusout="removeAriaDescribedBy"
      @blur="hideTooltip()"
      @dragstart="dragstart"
      @dragenter="dragenter"
      @dragend="dragend"
      @click="tileClick($event)"
    >
      <div
        :style="backgroundColor ? `background: ${backgroundColor}` : ''"
        :class="[
          'portal-tile__box',
          { 'portal-tile__box--draggable': editMode },
        ]"
      >
        <!-- alt on Image needs to be empty (it does not provide more and usefull information) -->
        <img
          :src="pathToLogo || './questionMark.svg'"
          onerror="this.src='./questionMark.svg'"
          alt=""
          class="portal-tile__img"
        >
      </div>
      <span class="portal-tile__name">
        {{ $localized(title) }}
      </span>

      <icon-button
        v-if="!minified && editMode"
        icon="edit-2"
        :active-at="activeAtEdit"
        class="portal-tile__edit-button icon-button--admin"
        :aria-label-prop="ariaLabelEditTile"
        @click="editTile"
      />
    </tabindex-element>
    <icon-button
      v-if="!minified && isTouchDevice"
      icon="info"
      class="portal-tile__info-button icon-button--admin"
      :aria-label-prop="ariaLabelInfoButton"
      @click="toolTipTouchHandler()"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';

import IconButton from '@/components/globals/IconButton.vue';
import TabindexElement from '@/components/activity/TabindexElement.vue';

import TileClick from '@/mixins/TileClick.vue';
import Draggable from '@/mixins/Draggable.vue';

import { Title, Description } from '@/store/modules/portalData/portalData.models';

interface PortalTile {
  tileId: string,
}

export default defineComponent({
  name: 'PortalTile',
  components: {
    IconButton,
    TabindexElement,
  },
  mixins: [
    TileClick,
    Draggable,
  ],
  props: {
    id: {
      type: String,
      default: '',
    },
    dn: {
      type: String,
      required: true,
    },
    superDn: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<Title>,
      required: true,
    },
    description: {
      type: Object as PropType<Description>,
      required: true,
    },
    activated: {
      type: Boolean,
      required: false,
    },
    anonymous: {
      type: Boolean,
      required: false,
    },
    backgroundColor: {
      type: String,
      default: '',
    },
    originalLinkTarget: {
      type: String,
      required: true,
    },
    minified: {
      type: Boolean,
      default: false,
    },
    fromFolder: {
      type: Boolean,
      default: false,
    },
  },
  data(): PortalTile {
    return {
      tileId: '',
    };
  },
  computed: {
    ...mapGetters({
      tooltip: 'tooltip/tooltip',
    }),
    wrapperTag(): string {
      return (this.minified || this.editMode) ? 'div' : 'a';
    },
    isTouchDevice(): boolean {
      return 'ontouchstart' in document.documentElement;
    },
    ariaLabelPortalTile(): null | string {
      return (this.minified || this.editMode) ? null : this.$localized(this.title);
    },
    ariaLabelInfoButton(): string {
      return `${this.$translateLabel('SHOW_TOOLTIP_BY_TOUCH')}`;
    },
    ariaLabelEditTile(): string {
      return this.$translateLabel('EDIT_TILE');
    },
    activeAtEdit(): string[] {
      if (!this.editMode) {
        return [];
      }
      if (this.fromFolder) {
        return ['modal'];
      }
      return ['portal'];
    },
    activeAt(): string[] {
      if (this.minified) {
        return [];
      }
      if (this.editMode) {
        return [];
      }
      if (this.fromFolder) {
        return ['modal'];
      }
      return ['portal', 'header-search'];
    },
  },
  mounted() {
    if (this.hasFocus) {
      this.$el.children[0].focus(); // sets focus to first Element in opened Folder
    }
  },
  updated() {
    console.log('updated!');
  },
  methods: {
    hideTooltip(): void {
      this.$store.dispatch('tooltip/unsetTooltip');
    },
    showTooltip(): void {
      if (!this.editMode && !this.minified) {
        const tooltip = {
          title: this.$localized(this.title),
          backgroundColor: this.backgroundColor,
          icon: this.pathToLogo,
          description: this.$localized(this.description),
          ariaId: this.createID(),
        };
        this.$store.dispatch('tooltip/setTooltip', { tooltip });
      }
    },
    editTile() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'AdminEntry',
        stubborn: true,
        props: {
          modelValue: this.$props,
          superDn: this.superDn,
          fromFolder: this.fromFolder,
          label: 'EDIT_ENTRY',
        },
      });
    },
    toolTipTouchHandler() {
      if (this.tooltip) {
        this.hideTooltip();
      } else {
        this.showTooltip();
      }
    },
    createID() {
      return `element-${this.$.uid}`;
    },
    setAriaDescribedBy() {
      this.tileId = this.createID();
    },
    removeAriaDescribedBy() {
      this.tileId = '';
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
  &__root-element
    display:flex
    justify-content: center
    position: relative
  &__box
    border-radius: var(--border-radius-apptile)
    display: flex
    align-items: center
    justify-content: center
    box-shadow: var(--box-shadow)
    background-color: var(--bgc-apptile-default)
    width: var(--app-tile-side-length)
    height: @width
    margin-bottom: calc(2 * var(--layout-spacing-unit))
    border: 0.2rem solid transparent
    box-sizing: border-box

    ~/:focus &
      border-color: var(--color-focus)

    &--draggable
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
    max-height: 80%

  &__name
    text-align: center
    width: 100%
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap
    text-shadow: 0 0.1rem 0.1rem rgba(0, 0, 0, 0.3)

  &__edit-button,
  &__info-button
    position: absolute
    top: -0.75em
    right: -0.75em
    z-index: $zindex-1

    &--in-modal
      position relative

  &__info-button
    font-size: var(--font-size-2)

    svg
      width: calc(1.5 * var(--button-icon-size))
      height: @width

  &__modal
    width: 650px
</style>
