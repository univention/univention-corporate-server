<!--
  Copyright 2021-2024 Univention GmbH

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
        class="portal-sidenavigation__link portal-sidenavigation__login"
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
      class="divider"
    />
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
          :target="item.target"
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
            aria-role="navigation"
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
    <div
      class="divider"
    />
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
    padding: 1em 0 1em 0
    cursor: pointer
    height: 36px
    position: relative
    left: 5%
    margin-top: var(--layout-spacing-unit)
    margin-bottom: calc(2*var(--layout-spacing-unit))
    width: fit-content
    font-size: var(--font-size-4)
    color: var(--font-color-contrast-high)
    font-weight: 600
    text-transform: uppercase
    font-family: 'Open Sans'
    background-color: rgba(0,0,0,0)
    border: 0.2rem solid rgba(0,0,0,0)
    transition: unset

    &:focus-visible
      border: 0.2rem solid var(--color-focus);
      outline: 0

  &__user-row
    display: flex
    height: $userRow
    font-weight: var(--font-weight-bold)

  &__user-icon
    position: relative
    overflow: hidden;
    border-radius: var(--border-radius-apptile)
    margin: 1rem
    border: 1px solid var(--portal-tab-background)
    width: 3rem
    height: @width
    margin: 24px 12px 24px 20px
    padding-left: 0 !important; // remove this line, when weird server caching is fixed

    svg
      fill: currentColor
      height: 3rem
      width: @height
      border-radius: var(--border-radius-circles)
      color: var(--portal-tab-background)
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

    &:hover
      text-decoration: underline

    &:focus-visible span
      text-decoration: none

  &__login
    width: 5rem
    margin-top: calc(2*var(--layout-spacing-unit))
    background-color: var(--button-primary-bgc)

    &:hover
      background-color: var(--button-primary-bgc-hover)

    span
        margin: 0.2rem

  &__login-header
    &:focus-visible
      outline: 0

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
      text-transform: uppercase
      padding-left: 4rem
      margin-bottom: 1rem
    &:hover
      background-color: var(--bgc-user-menu-item-hover)

  &__edit-mode
    background-color: var(--button-primary-bgc)
    border-radius: var(--border-radius-interactable)
    width: 6.5rem

    span
      margin: 0.2rem

    &:focus-visible span
      margin: 0

    &:hover
      background-color: var(--button-primary-bgc-hover)

  &__fade-left-right,
  &__fade-right-left
    animation-duration: 250ms

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

.divider
    background-color: var(--bgc-user-menu-item-hover)
    width: 90%
    height: 2px
    position: relative
    left: 5%
    margin-bottom: 8px
</style>
