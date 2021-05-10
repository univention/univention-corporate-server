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
  <nav class="portal-sidenavigation">
    <div class="portal-sidenavigation__login-header">
      <div
        v-if="userState.username"
        class="portal-sidenavigation__user-row"
      >
        <portal-icon
          icon="user"
        />
        <div>
          <div class="portal-sidenavigation--username">
            {{ userState.displayName }}
          </div>
          <!-- as long as this link has no href, this needs to be a button to be focusable -->
          <button
            id="loginButton"
            ref="loginButton"
            class="portal-sidenavigation__logout-link"
            @click="logout"
            @keydown.shift.tab.exact="focusOnLastItemInSideMenu($event)"
            @keydown.esc="closeNavigation"
          >
            <translate i18n-key="LOGOUT" />
          </button>
        </div>
      </div>
      <button
        v-else
        id="loginButton"
        ref="loginButton"
        class="portal-sidenavigation__link"
        @click="login"
        @keydown.shift.tab.exact="focusOnLastItemInSideMenu($event)"
        @keydown.esc="closeNavigation"
      >
        <translate i18n-key="LOGIN" />
      </button>
    </div>

    <div
      class="portal-sidenavigation__menu"
    >
      <div
        v-for="(item, index) in menuLinks"
        :key="index"
        :class="setFadeClass()"
        class="portal-sidenavigation__menu-item"
      >
        <menu-item
          v-if="menuVisible"
          :ref="'menuItem' + index"
          :links="[]"
          v-bind="item"
          :aria-haspopup="hasSubmenu(item)"
          @click="toggleMenu(index)"
          @keydown.up.exact.prevent="selectPrevious( 'menuItem', index, menuLinks.length)"
          @keydown.down.exact.prevent="selectNext( 'menuItem', index, menuLinks.length)"
          @keydown.enter.exact="focusOnChild(index)"
          @keydown.space.exact.prevent="focusOnChild(index)"
          @keydown.right.exact="focusOnChild(index)"
          @keydown.tab.exact="nextElementTab($event, index)"
          @keydown.esc="closeNavigation"
        />
        <template v-if="item.subMenu && item.subMenu.length > 0">
          <menu-item
            v-if="subMenuVisible & (menuParent === index)"
            ref="subItemParent"
            :title="item.title"
            :is-sub-item="true"
            :links="[]"
            class="portal-sidenavigation__menu-subItem portal-sidenavigation__menu-subItem--parent"
            @click="toggleMenu()"
            @keydown.enter.exact.prevent="focusOnParent(index)"
            @keydown.space.exact.prevent="focusOnParent(index)"
            @keydown.left.exact="focusOnParent(index)"
            @keydown.up.exact.prevent="selectPrevious('subItemParent',index, item.subMenu.length)"
            @keydown.down.exact.prevent="selectNext('subItemParent', index)"
            @keydown.esc="closeNavigation"
          />
          <div
            v-for="(subItem, subindex) in item.subMenu"
            :key="subindex"
            :class="subMenuClass"
          >
            <menu-item
              v-if="subMenuVisible & (menuParent === index)"
              :ref="`subItem${subindex}`"
              v-bind="subItem"
              class="portal-sidenavigation__menu-subItem"
              @clickAction="closeNavigation"
              @keydown.up.prevent="selectPrevious('subItem', subindex, item.subMenu.length)"
              @keydown.down.prevent="selectNext('subItem', subindex, item.subMenu.length)"
              @keydown.esc="closeNavigation"
            />
          </div>
        </template>
      </div>
    </div>

    <button
      v-if="userState.mayEditPortal"
      ref="editModeButton"
      class="portal-sidenavigation__link portal-sidenavigation__edit-mode"
      @click="startEditMode"
      @keydown.esc="closeNavigation"
      @keydown.tab.exact.prevent="focusOnLoginButton"
    >
      <translate
        i18n-key="EDIT_PORTAL"
      />
    </button>
  </nav>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import MenuItem from '@/components/navigation/MenuItem.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

import { login, logout } from '@/jsHelper/login';
import Translate from '@/i18n/Translate.vue';

interface SideNavigationData {
  menuVisible: boolean,
  subMenuVisible: boolean,
  subMenuClass: string,
  menuParent: number,
  init: boolean,
  fade: boolean,
  fadeRightLeft: string,
  fadeLeftRight: string,
  changeLanguageTranslation: unknown
}

export default defineComponent({
  name: 'SideNavigation',
  components: {
    PortalIcon,
    MenuItem,
    Translate,
  },
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
      // TODO: outsource translation
      changeLanguageTranslation: {
        de_DE: 'Sprache ändern',
        en_US: 'Change language',
      },
    };
  },
  computed: {
    ...mapGetters({
      menuLinks: 'menu/getMenu',
      editMode: 'portalData/editMode',
      userState: 'user/userState',
      meta: 'metaData/getMeta',
    }),
  },
  mounted() {
    this.focusOnLoginButton();
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
      document.getElementById('header-button-menu')?.focus();
    },
    toggleMenu(index = -1): void {
      this.menuVisible = !this.menuVisible;
      this.menuParent = index;
      this.subMenuVisible = !this.subMenuVisible;
      this.fade = !this.fade;
      this.init = false;

      if (this.subMenuVisible) {
        this.subMenuClass = 'portal-sidenavigation__menu-item--show';
      } else {
        this.subMenuClass = 'portal-sidenavigation__menu-item--hide';
      }
    },
    async startEditMode(): Promise<void> {
      await this.$store.dispatch('portalData/setEditMode', true);
      this.$store.dispatch('navigation/setActiveButton', 'settings');
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
    selectPrevious(menuReference: string, index?: number, numberOfItems?: number): void {
      // test
      if (menuReference === 'subItemParent') {
        console.log('selectPrevious: in subMenu');
        // If current is subitem Parent focus last item in list
        this.$nextTick(() => {
          const lastChildIndex = numberOfItems ? numberOfItems - 1 : null;
          const firstSubItemChild = (this.$refs[`subItem${lastChildIndex}`] as HTMLFormElement).$el;
          firstSubItemChild.focus();
        });
      } else if (menuReference === 'subItem' || menuReference === 'menuItem') {
        console.log('selectPrevious: in parentMenu');
        if (index === 0) {
          console.log('selectPrevious: ?');
          // If current is first submenu item set focus to subItemParent.
          if (menuReference === 'subItem') {
            console.log('selectPrevious: !');
            this.focusOnSubItemParent();
          } else {
            console.log('selectPrevious: ?');
            const lastElementIndex = numberOfItems ? numberOfItems - 1 : null;
            (this.$refs[`menuItem${lastElementIndex}`] as HTMLFormElement).$el.focus();
          }
        } else {
          console.log('selectPrevious: normal previous behaviour');
          // normal previous behaviour
          const currentElement = (this.$refs[menuReference + index] as HTMLFormElement).$el;
          const previousElement = currentElement.parentElement.previousElementSibling.children[0];
          previousElement.focus();
        }
      }
    },
    selectNext(menuReference: string, index?: number, numberOfItems?: number): void {
      if (menuReference === 'subItemParent') {
        this.$nextTick(() => {
          const firstSubItemChild = (this.$refs.subItem0 as HTMLFormElement).$el;
          firstSubItemChild.focus();
        });
      } else {
        const currentElement = (this.$refs[menuReference + index] as HTMLFormElement).$el;
        const lastChildIndex = numberOfItems ? numberOfItems - 1 : null;
        if (index === lastChildIndex) {
          if (menuReference === 'subItem') {
            this.focusOnSubItemParent();
          } else {
            (this.$refs.menuItem0 as HTMLFormElement).$el.focus();
          }
        } else {
          const nextElement = currentElement.parentElement.nextElementSibling.children[0];
          nextElement.focus();
        }
      }
    },
    hasSubmenu(item): boolean {
      return item.subMenu && item.subMenu.length > 0;
    },
    focusOnChild(index): void {
      this.toggleMenu(index);
      this.$nextTick(() => {
        this.focusOnSubItemParent();
      });
    },
    focusOnParent(index): void {
      this.toggleMenu(index);
      this.$nextTick(() => {
        const parentMenuItem = (this.$refs[`menuItem${index}`] as HTMLFormElement).$el;
        parentMenuItem.focus();
      });
    },
    focusOnSubItemParent(): void {
      (this.$refs.subItemParent as HTMLFormElement).$el.focus();
    },
    focusOnLastItemInSideMenu(event): void {
      // call this to trap user in side navigation
      event.preventDefault();
      if (this.userState.mayEditPortal) {
        this.focusOnEditModeButton();
      } else {
        const lastElementIndex = this.menuLinks.length - 1;
        const lastMenuItem = (this.$refs[`menuItem${lastElementIndex}`] as HTMLFormElement) ? (this.$refs[`menuItem${lastElementIndex}`] as HTMLFormElement).$el : null;
        if (lastMenuItem) {
          // focus to last element of menu
          lastMenuItem.focus();
        } else {
          // if submenu is open the focus should go on last submenuitem
          const subMenuItems = Object.keys(this.$refs).filter((refTitle) => refTitle.includes('subItem'));
          const lastSubMenuItemReference = subMenuItems[subMenuItems.length - 1];
          (this.$refs[lastSubMenuItemReference] as HTMLFormElement).$el.focus();
        }
      }
    },
    focusOnLoginButton(): void {
      (this.$refs.loginButton as HTMLFormElement).focus();
    },
    focusOnEditModeButton(): void {
      (this.$refs.editModeButton as HTMLFormElement).focus();
    },
    nextElementTab(event, index?: number): void {
      // only call this on last Menu Item to trap user in side navigation
      const lastElementIndex = this.menuLinks.length - 1;
      if (index === lastElementIndex) {
        event.preventDefault();
        if (this.userState.mayEditPortal) {
          this.focusOnEditModeButton();
        } else {
          this.focusOnLoginButton();
        }
      }
    },
  },
});
</script>

<style lang="stylus">
.portal-sidenavigation
  height: calc(100vh - (var(--portal-header-height) + 0.5rem))
  display: flex
  flex-direction: column
  align-item: flex-end

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
    &:hover
      background-color: #272726
    &:focus
      border: 0.2rem solid var(--color-focus);
      outline: 0
  &__user-row
    padding-left: var(--layout-spacing-unit)
    display: flex
    height: 6rem
    font-weight: var(--font-weight-bold)

    svg
      fill: currentColor
      height: 4rem
      width: @height
      background-color: var(--color-grey40)
      margin: 1rem
      border-radius: var(--border-radius-circles)
    &> div
      margin: auto 0
      padding-left: var(--layout-spacing-unit)
  &--username
    padding-left: 3px

  &__logout-link
    cursor: pointer
    background-color: rgba(0,0,0,0)
    color: var(--font-color-contrast-high)
    font-size: var(--font-size-4)
    border: 0.2rem solid rgba(0,0,0,0);

    &:hover
      background-color: #272726
    &:focus
      border: 0.2rem solid var(--color-focus);
      outline: 0

    span
      text-decoration: underline

  &__login-header
    border-bottom: 4px solid var(--color-grey8)

  &__menu
    margin: 0
    margin-bottom: auto
    padding-left: 0

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
    border-top: 0.4rem solid var(--color-grey8)

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
