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
  <div class="tile-add__wrapper">
    <div
      class="tile-add"
      @click="showMenu()"
    >
      <portal-icon
        icon="plus"
        icon-width="100%"
      />
    </div>

    <div
      v-if="popMenuShow"
      class="tile-add__menu-wrapper"
    >
      <div class="tile-add__menu-container">
        <div
          v-for="(item, index) in popMenu"
          :key="index"
          class="tile-add__menu-parent"
          @mouseover="showChildren(item.parent.children, index)"
        >
          <span class="tile-add__title">
            {{ item.parent.title.de_DE }}
          </span>

          <portal-icon
            icon="chevron-right"
            icon-width="2rem"
            class="tile-add__icon"
          />
        </div>
      </div>

      <div
        v-if="menuChildren.length > 0"
        class="tile-add__menu-container tile-add__menu-children"
        :style="`top: calc(42px * ${popMenuOffset})`"
      >
        <div
          v-for="(child, index) in menuChildren"
          :key="index"
          class="tile-add__menu-child"
        >
          {{ child.title.de_DE }}
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';
// mocks
import PopMenuData from '@/assets/data/popmenu.json';

interface TileAddData {
  popMenu: Record<string, unknown>[],
  menuChildren: Record<string, unknown>[],
  popMenuOffset: number,
  popMenuShow: boolean,
}

export default defineComponent({
  name: 'TileAdd',
  components: {
    PortalIcon,
  },
  data(): TileAddData {
    return {
      popMenu: PopMenuData,
      menuChildren: [],
      popMenuOffset: 0,
      popMenuShow: false,
    };
  },
  created() {
    window.addEventListener('click', (e) => {
      if (!this.$el.contains(e.target)) {
        this.hideMenu();
      }
    });
  },
  unmounted() {
    window.removeEventListener('click', (e) => {
      console.info('listener removed', this.$el.contains(e.target));
    });
  },
  methods: {
    showMenu(): void {
      this.popMenuShow = !this.popMenuShow;

      if (!this.popMenuShow) {
        this.menuChildren = [];
      }
    },
    showChildren(children: Record<string, unknown>[], index: number): void {
      this.menuChildren = children;
      this.popMenuOffset = index;
    },
    hideMenu(): void {
      this.popMenuShow = false;
      this.menuChildren = [];
    },
  },
});
</script>

<style lang="stylus">
.tile-add
  margin: 0
  min-width: var(--app-tile-side-length)
  width: var(--app-tile-side-length)
  height: var(--app-tile-side-length)
  border-radius: 15%
  border: 3px solid var(--color-grey40)
  background-color: transparent
  background-position: center
  background-size: 3em
  background-repeat: no-repeat
  cursor: pointer

  svg
    stroke: var(--color-grey40)

  &__wrapper
    position: relative

  &__menu-wrapper
    width: 100%
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    justify-content: flex-start;
    align-content: flex-start;
    align-items: flex-start;
    position: absolute

  &__menu-container
    min-width: var(--app-tile-side-length)
    position: relative
    order: 0;
    flex: 0 1 auto;
    align-self: auto;

  &__icon
    position: absolute
    right: 15px
    margin-top: 2px

  &__menu-parent,
  &__menu-child
    background: var(--color-grey0)
    padding: 0.3em 0.5em;
    min-width: var(--app-tile-side-length)
    font-size: 16px

    &:hover
      background: #000
      cursor: pointer

    &:first-of-type
      border-radius: 8px 8px 0 0
    &:last-of-type
      border-radius: 0 0 8px 8px

  &__menu-child
    min-width: var(--app-tile-side-length)
    white-space: nowrap
</style>
