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
  <tabindex-element
    :id="id"
    :tag="link ? 'a' : 'div'"
    :active-at="activeAt"
    class="menu-item"
    :class="{ 'menu-item__disabled': disabled }"
    :href="link ? link : null"
    :target="anchorTarget"
    :role="ariaRole"
    :aria-disabled="ariaDisabled"
    @click="setClickIfSubItem"
    @keydown.enter="setClickIfSubItem"
    @keydown.space="setClickIfSubItem"
  >
    <portal-icon
      v-if="isParentInSubItem"
      icon="chevron-left"
      class="menu-item__arrow menu-item__arrow--left"
    />
    {{ $localized(title) }}
    <template
      v-if="subMenu.length > 0"
    >
      <div
        class="menu-item__counter"
      >
        {{ subMenu.length }}
        <span class="sr-only sr-only-mobile">
          {{ itemString }}
        </span>
      </div>
      <portal-icon
        v-if="!isParentInSubItem"
        icon="chevron-right"
        class="menu-item__arrow menu-item__arrow--right"
      />
    </template>
  </tabindex-element>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import _ from '@/jsHelper/translate';
import { mapGetters } from 'vuex';

import TabindexElement from '@/components/activity/TabindexElement.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import TileClick from '@/mixins/TileClick.vue';

import { Locale } from '@/store/modules/locale/locale.models';

export default defineComponent({
  name: 'MenuItem',
  components: {
    PortalIcon,
    TabindexElement,
  },
  mixins: [
    TileClick,
  ],
  props: {
    id: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<Record<Locale, string>>,
      required: true,
    },
    subMenu: {
      type: Array,
      default: () => [],
    },
    isParentInSubItem: {
      type: Boolean,
      default: false,
    },
    isSubitem: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    ...mapGetters({
      disabledMenuItems: 'menu/disabledMenuItems',
    }),
    disabled(): boolean {
      return this.disabledMenuItems.includes(this.id);
    },
    ariaDisabled(): boolean {
      return this.ariaRole === 'button' && this.disabled;
    },
    activeAt(): string[] {
      return ['header-menu'];
    },
    itemString(): string {
      const numberOfItems = this.subMenu.length;
      let itemString = '';
      if (numberOfItems === 0) {
        itemString = _('No items');
      } else if (numberOfItems === 1) {
        itemString = _('Item');
      } else {
        itemString = _('Items');
      }
      return itemString;
    },
    ariaRole(): string {
      return this.link ? 'link' : 'button';
    },
  },
  methods: {
    setClickIfSubItem($event) {
      if (this.isSubitem) {
        // @ts-ignore
        this.tileClick($event);
      }
    },
  },
});
</script>

<style lang="stylus">
.menu-item
  position: relative;
  z-index: 15;
  display: flex;
  align-items: center;
  padding: 1em 0 1em 20px;
  color: inherit;
  text-decoration: none;
  border: 0.2rem solid rgba(0,0,0,0);

  &:hover
    cursor: pointer;

  &:focus
    outline: 0;
    border: 0.2rem solid var(--color-focus);

  &__disabled
    pointer-events: none
    color: var(--font-color-contrast-low)

  &__counter
    position: absolute;
    right: 0;
    margin-right: 4rem;
    display: inline;

  &__arrow
    position: absolute;
    display: inline;
    font-size: inherit;
    width: 1rem;
    height: 1rem;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
    fill: none;
    transition: color var(--portal-transition-duration);
    &--left
      left: 1.2rem;
    &--right
      right: 0;
      margin-right: 1.2rem;
</style>
