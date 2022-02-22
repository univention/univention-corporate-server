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
  <region
    id="portal-sidenavigation"
    role="navigation"
    direction="topdown"
    class="portal-sidenavigation"
  >
    <div class="portal-sidenavigation__login-header">
      <div
        v-if="userState.username"
        class="portal-sidenavigation__user-row"
      >
        <div class="portal-sidenavigation__user-icon">
          <portal-icon
            icon="user"
          />
        </div>
        <div class="portal-sidenavigation__user-text-content">
          <div class="portal-sidenavigation--username">
            {{ userState.displayName }}
          </div>
          <div
            id="loginButton"
            ref="loginButton"
            class="portal-sidenavigation__logout-link"
            tabindex="0"
            role="button"
            @click="logout"
            @keydown.enter="logout"
            @keydown.esc="closeNavigation"
          >
            <span>
              {{ LOGOUT }}
            </span>
          </div>
        </div>
      </div>
      <button
        v-else
        id="loginButton"
        ref="loginButton"
        class="portal-sidenavigation__link"
        @click="login"
        @keydown.enter="login"
        @keydown.esc="closeNavigation"
      >
        <span>
          {{ LOGIN }}
        </span>
      </button>
    </div>

    <div
      class="portal-sidenavigation__menu"
      role="toolbar"
      aria-orientation="vertical"
    >
      <div
        v-for="(item, index) in menuLinks"
        :key="index"
        :class="setFadeClass()"
        class="portal-sidenavigation__menu-item"
      >
        <menu-item
          v-if="menuVisible"
          :id="item.id"
          :ref="'menuItem' + index"
          :title="item.title"
          :sub-menu="item.subMenu"
          :links="item.links || []"
          :link-target="item.linkTarget"
          :path-to-logo="item.pathToLogo"
          :internal-function="item.internalFunction"
          :background-color="item.backgroundColor"
          :aria-haspopup="hasSubmenu(item)"
          @click="menuClickAction($event, index, item)"
          @keydown.enter.exact="menuClickAction($event, index, item)"
          @keydown.space.exact="menuClickAction($event, index, item)"
          @keydown.right.exact.prevent="hasSubmenu(item) ? toggleMenu(index) : null"
          @keydown.esc="closeNavigation"
          @clickAction="closeNavigation"
        />
        <template v-if="hasSubmenu(item)">
          <region
            v-if="subMenuVisible & (menuParent === index)"
            id="portal-sidenavigation-sub"
            class="portal-sidenavigation__submenu"
            role="navigation"
            direction="topdown"
            :aria-expanded="subMenuVisible"
          >
            <menu-item
              :id="`sub-item-${item.id}`"
              :title="item.title"
              :is-parent-in-sub-item="true"
              :links="[]"
              class="portal-sidenavigation__menu-subItem portal-sidenavigation__menu-subItem--parent"
              @click="toggleMenu()"
              @keydown.enter.exact="toggleMenu()"
              @keydown.space.exact.prevent="toggleMenu()"
              @keydown.left.exact="toggleMenu()"
              @keydown.esc="closeNavigation"
              @clickAction="closeNavigation"
            />
            <div
              v-for="(subItem, subindex) in item.subMenu"
              :key="subindex"
              :class="subMenuClass"
            >
              <menu-item
                v-if="subMenuVisible & (menuParent === index)"
                :id="subItem.id"
                :ref="`subItem${subindex}`"
                :title="subItem.title"
                :links="subItem.links || []"
                :link-target="subItem.linkTarget"
                :path-to-logo="subItem.pathToLogo"
                :internal-function="subItem.internalFunction"
                :background-color="subItem.backgroundColor"
                :is-subitem="true"
                class="portal-sidenavigation__menu-subItem"
                @keydown.esc="closeNavigation"
                @clickAction="closeNavigation"
              />
            </div>
          </region>
        </template>
      </div>
    </div>

    <button
      v-if="userState.mayEditPortal"
      ref="editModeButton"
      class="portal-sidenavigation__link portal-sidenavigation__edit-mode"
      data-test="openEditmodeButton"
      @click="startEditMode"
      @keydown.esc="closeNavigation"
    >
      {{ EDIT_PORTAL }}
    </button>
  </region>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import Region from '@/components/activity/Region.vue';
import MenuItem from '@/components/navigation/MenuItem.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import TileClick from '@/mixins/TileClick.vue';

import { login, logout } from '@/jsHelper/login';

interface SideNavigationData {
  menuVisible: boolean,
  subMenuVisible: boolean,
  subMenuClass: string,
  menuParent: number,
  init: boolean,
  fade: boolean,
  fadeRightLeft: string,
  fadeLeftRight: string,
}

export default defineComponent({
  name: 'SideNavigation',
  components: {
    PortalIcon,
    MenuItem,
    Region,
  },
  mixins: [
    TileClick,
  ],
  data(): SideNavigationData {
    return {
      menuVisible: true,
      subMenuVisible: false,
      subMenuClass: 'portal-sidenavigation__menu-item--hide',
      menuParent: -1,
      init: true,
      fade: false,
      fadeRightLeft: 'portal-sidenavigation__fade-right-left',
      fadeLeftRight: 'portal-sidenavigation__fade-left-right',
    };
  },
  computed: {
    ...mapGetters({
      menuLinks: 'menu/getMenu',
      editMode: 'portalData/editMode',
      userState: 'user/userState',
      meta: 'metaData/getMeta',
    }),
    LOGOUT(): string {
      return _('Logout');
    },
    LOGIN(): string {
      return _('Login');
    },
    GO_BACK(): string {
      return _('Go Back');
    },
    EDIT_PORTAL(): string {
      return _('Edit portal');
    },
    CHANGE_LANGUAGE(): string {
      return _('Change language');
    },
  },
  mounted(): void {
    this.$store.dispatch('activity/setRegion', 'portal-sidenavigation');
  },
  methods: {
    login(): void {
      login(this.userState);
    },
    logout(): void {
      logout();
    },
    closeNavigation(): void {
      this.$store.dispatch('navigation/setActiveButton', '');
      this.$store.dispatch('activity/setRegion', 'portal-header');
    },
    toggleMenu(index = -1): void {
      this.menuVisible = !this.menuVisible;
      this.menuParent = index;
      this.subMenuVisible = !this.subMenuVisible;
      this.fade = !this.fade;
      this.init = false;

      const region = index === -1 ? 'portal-sidenavigation' : 'portal-sidenavigation-sub';
      this.$store.dispatch('activity/setRegion', region);

      if (this.subMenuVisible) {
        this.subMenuClass = 'portal-sidenavigation__menu-item--show';
      } else {
        this.subMenuClass = 'portal-sidenavigation__menu-item--hide';
      }
    },
    async startEditMode(): Promise<void> {
      await this.$store.dispatch('portalData/setEditMode', true);
      (this.$refs.editModeButton as HTMLElement).blur();
      this.$store.dispatch('navigation/setActiveButton', '');
      this.$store.dispatch('tabs/setActiveTab', 0);
    },
    setFadeClass(): string {
      let ret = '';
      if (!this.init) {
        if (!this.fade) {
          ret = this.fadeLeftRight;
        } else {
          ret = this.fadeRightLeft;
        }
      }
      return ret;
    },
    hasSubmenu(item): boolean {
      return item.subMenu && item.subMenu.length > 0;
    },
    menuClickAction($event, index: number, item: Record<string, unknown>): void {
      if (this.hasSubmenu(item)) {
        $event.preventDefault();
        this.toggleMenu(index);
      } else {
        const menuItem = this.$refs[`menuItem${index}`] ? this.$refs[`menuItem${index}`] : this.$refs[`subItem${index}`];
        // @ts-ignore
        menuItem.tileClick($event);
        if (item.linkTarget === 'embedded') {
          this.$store.dispatch('navigation/setActiveButton', '');
          this.$store.dispatch('activity/saveFocus', {
            region: 'portal-sidenavigation',
            id: 'loginButton',
          });
        }
      }
    },
  },
});
</script>

<style lang="stylus">
$userRow = 6rem
.portal-sidenavigation
  height: 100%
  display: flex
  flex-direction: column

  &__link
    padding: 1em 0 1em 20px
    cursor: pointer
    height: auto
    width: 100%
    justify-content: left
    font-size: var(--font-size-4)
    color: var(--font-color-contrast-high)
    font-weight: 600
    text-transform: uppercase
    background-color: rgba(0,0,0,0)
    border: 0.2rem solid rgba(0,0,0,0)
    &:focus
      border: 0.2rem solid var(--color-focus);
      outline: 0
  &__user-row
    padding-left: var(--layout-spacing-unit)
    display: flex
    height: $userRow
    font-weight: var(--font-weight-bold)
  &__user-icon
    position: relative
    overflow: hidden;
    border-radius: 100%
    margin: 1rem
    border: 1px solid var(--font-color-contrast-high)
    width: 4rem
    height: @width
    margin: 1rem 1rem 1rem 0
    padding-left: 0 !important; // remove this line, when weird server caching is fixed

    svg
      fill: currentColor
      height: 4rem
      width: @height
      border-radius: var(--border-radius-circles)
      margin: 0

  &__user-text-content
    margin: auto 0
    padding: 0 var(--layout-spacing-unit)
    height: 100%;
    align-items: flex-start
    display: flex
    flex-direction: column
    justify-content: space-between
    padding: calc(1rem + var(--layout-spacing-unit)) 0
    box-sizing: border-box

  &--username
    font-weight: bold

  &__logout-link
    cursor: pointer
    background-color: rgba(0,0,0,0)
    color: var(--font-color-contrast-high)
    font-size: var(--font-size-4)
    border-bottom: 0.2rem solid rgba(0,0,0,0);
    font-weight: normal
    width: min-content

    &:focus
      text-decoration: underline
      outline: 0

    &:focus span
      text-decoration: none

  &__login-header
    border-bottom: 4px solid var(--bgc-content-body)

  &__menu
    flex: 1 1 auto
    overflow-y: auto
    overflow-x: hidden

  &__menu-item
    margin-left: 0

    &--show
      display: block

    &--hide
      display: none

  &__menu-subItem
    margin-left: 0
    &--parent
      text-transform: uppercase;
      padding-left: 4rem;

  &__edit-mode
    border-radius: unset
    border: 0.2rem solid var(--bgc-content-container)
    border-top-color: var(--bgc-content-body)

    span
      margin: 0.2rem

    &:focus span
      margin: 0

  &__fade-left-right,
  &__fade-right-left
    animation-duration: .4s;

  &__fade-right-left
    animation-name: fadeOutRight

  &__fade-left-right
    animation-name: fadeInLeft

// keyframes
@keyframes fadeInLeft {
  0% {
    opacity: 0;
    transform: translateX(20rem);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeOutRight {
  0% {
    opacity: 0;
    transform: translateX(20rem);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
