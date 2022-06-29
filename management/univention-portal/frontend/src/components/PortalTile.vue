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
  <div class="portal-tile__root-element">
    <tabindex-element
      :id="id"
      :tag="wrapperTag"
      :active-at="activeAt"
      :href="link"
      :to="link"
      :target="anchorTarget"
      :aria-describedby="tileId"
      :aria-label="ariaLabelPortalTile"
      :draggable="editMode && !minified"
      :disabled="isDisabled"
      :class="{
        'portal-tile--minified': minified,
      }"
      class="portal-tile"
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
          { 'portal-tile__box--draggable': editMode,
            'portal-tile__box--dragging': isBeingDragged,
          }
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
      <div
        :id="tileId"
        class="sr-only sr-only-mobile"
      >
        {{ $localized(description) }}
      </div>

      <div class="portal-tile__icon-bar">
        <icon-button
          v-if="!minified && editMode && showEditButtonWhileDragging"
          icon="edit-2"
          :active-at="activeAtEdit"
          class="icon-button--admin"
          :aria-label-prop="EDIT_ENTRY"
          @click="editTile"
        />
        <icon-button
          v-if="!minified && editMode && !isTouchDevice && showMoveButtonWhileDragging"
          :id="`${layoutId}-move-button`"
          ref="mover"
          icon="move"
          :active-at="activeAtEdit"
          class="icon-button--admin"
          :aria-label-prop="MOVE_ENTRY"
          role="button"
          @click="dragKeyboardClick"
          @keydown.esc="dragend"
          @keydown.left="dragKeyboardDirection($event, 'left', dragAndDropData)"
          @keydown.right="dragKeyboardDirection($event, 'right', dragAndDropData)"
          @keydown.up="dragKeyboardDirection($event, 'up',dragAndDropData)"
          @keydown.down="dragKeyboardDirection($event, 'down', dragAndDropData)"
          @keydown.tab="handleTabWhileMoving"
        />
      </div>
    </tabindex-element>
    <icon-button
      v-if="!minified && isTouchDevice && !editMode"
      icon="info"
      class="portal-tile__info-button icon-button--admin"
      :aria-label-prop="SHOW_TOOLTIP"
      @click="toolTipTouchHandler()"
    />
  </div>
</template>

<script lang="ts">
// TODO remove extra attributes on tabindex-element depending on tag (?) e.g. in edit mode the <div>s have href set

import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import TabindexElement from '@/components/activity/TabindexElement.vue';

import TileClick from '@/mixins/TileClick.vue';
import Draggable from '@/mixins/Draggable.vue';

import { LocalizedString } from '@/store/modules/portalData/portalData.models';

interface PortalTile {
  tileId: string,
  mouseIsOverTile: boolean,
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
    layoutId: {
      type: String,
      required: true,
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
      type: Object as PropType<LocalizedString>,
      required: true,
    },
    description: {
      type: Object as PropType<LocalizedString>,
      required: true,
    },
    keywords: {
      type: Object as PropType<LocalizedString>,
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
    allowedGroups: {
      type: Array,
      default: () => [],
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
      mouseIsOverTile: false,
    };
  },
  computed: {
    ...mapGetters({
      tooltip: 'tooltip/tooltip',
      tooltipIsHovered: 'tooltip/tooltipIsHovered',
      tooltipID: 'tooltip/getTooltipID',
      lastDir: 'dragndrop/getLastDir',
    }),
    wrapperTag(): string {
      if (this.linkTarget === 'internalrouter') {
        return 'router-link';
      }
      return (this.minified || this.editMode) ? 'div' : 'a';
    },
    isDisabled(): boolean {
      return (this.minified || this.editMode);
    },
    isTouchDevice(): boolean {
      return 'ontouchstart' in document.documentElement;
    },
    ariaLabelPortalTile(): null | string {
      return (this.minified || this.editMode) ? null : `${this.$localized(this.title)} ${this.LINK_TYPE(this.linkTarget).label}`;
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
    MOVE_ENTRY(): string {
      return _('Move tile: %(entry)s', { entry: this.$localized(this.title) });
    },
    EDIT_ENTRY(): string {
      return _('Edit tile: %(entry)s', { entry: this.$localized(this.title) });
    },
    SHOW_TOOLTIP(): string {
      return _('Show tooltip');
    },
    LINK_TYPE_LABEL(): string {
      return this.LINK_TYPE(this.linkTarget).label;
    },
    isMobile(): boolean {
      return this.isTouchDevice && !this.minified;
    },
  },
  mounted() {
    if (this.hasFocus) {
      this.$el.children[0].focus(); // sets focus to first Element in opened Folder
    }
    if (this.$refs.mover) {
      // @ts-ignore
      this.handleDragFocus(this.$refs.mover.$el, this.lastDir);
    }
  },
  methods: {
    hideTooltip(): void {
      this.mouseIsOverTile = false;
      if (this.tooltipID && !this.tooltipIsHovered) {
        this.$store.dispatch('tooltip/unsetTooltip');
      }
    },
    showTooltip(): void {
      this.$store.dispatch('tooltip/unsetTooltip');
      clearTimeout(this.tooltipID);
      this.mouseIsOverTile = true;
      if (!this.editMode && !this.minified) {
        const portalTileNameRect = this.$el.querySelector('.portal-tile__name').getBoundingClientRect();
        const portalTileRect = this.$el.getBoundingClientRect();
        const linkTypeText = this.LINK_TYPE(this.linkTarget);
        const tooltip = {
          linkType: linkTypeText,
          isMobile: this.isMobile,
          title: this.$localized(this.title),
          backgroundColor: this.backgroundColor,
          description: this.$localized(this.description),
          ariaId: this.createID(),
          position: {
            top: portalTileRect.top,
            right: portalTileRect.right,
            bottom: portalTileNameRect.bottom,
            left: portalTileRect.left,
            x: portalTileRect.x,
            y: portalTileRect.y,
          },
        };
        this.setToolTipTimeOut(tooltip);
      }
    },
    setToolTipTimeOut(tooltip): void {
      const id = setTimeout(() => {
        console.log('Already IN');
        if (this.mouseIsOverTile === true) {
          this.$store.dispatch('tooltip/setTooltip', { tooltip });
        }
      }, 650);
      this.$store.dispatch('tooltip/setTooltipID', id);
    },
    editTile() {
      this.$store.dispatch('modal/setAndShowModal', {
        name: 'AdminEntry',
        stubborn: true,
        props: {
          modelValue: this.$props,
          superDn: this.superDn,
          fromFolder: this.fromFolder,
          label: _('Edit entry'),
        },
      });
    },
    toolTipTouchHandler() {
      if (this.tooltip && this.tooltip.description === this.$localized(this.description)) {
        this.hideTooltip();
        this.$store.dispatch('activity/setMessage', _('Tooltip hidden'));
      } else {
        this.showTooltip();
        this.$store.dispatch('activity/setMessage', _('Tooltip displayed'));
        setTimeout(() => {
          this.$store.dispatch('activity/setMessage', this.$localized(this.description));
        }, 50);
      }
    },
    createID(): string {
      return `element-${this.$.uid}`;
    },
    setAriaDescribedBy(): void {
      this.tileId = this.createID();
    },
    removeAriaDescribedBy():void {
      this.tileId = '';
    },
    LINK_TYPE(linkTarget): Record<string, string> {
      const target = (linkTarget === 'samewindow') && ((this.link as string).includes('.crt') || (this.link as string).includes('.crl')) ? 'download' : linkTarget;
      const linkTypes = {
        samewindow: {
          label: _('Same tab'),
          icon: 'sidebar',
        },
        newwindow: {
          label: _('New Tab'),
          icon: 'external-link',
        },
        embedded: {
          label: _('iFrame'),
          icon: 'layout',
        },
        download: {
          label: _('Download'),
          icon: 'download',
        },
      };
      return linkTypes[target];
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

    &--dragged-line
      border: 3px solid pink

    &--dragging
      transform: rotate(-10deg)
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
    word-wrap: break-word
    hyphens: auto

  &__info-button,
  &__icon-bar
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
