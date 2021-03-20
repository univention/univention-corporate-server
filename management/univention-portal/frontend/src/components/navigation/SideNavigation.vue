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
          icon-width="6rem"
        />
        <div>
          <div class="portal-sidenavigation--username">
            {{ userState.displayName }}
          </div>
          <button
            ref="loginButton"
            class="portal-sidenavigation__logout-link"
            @click="logout"
            @keydown.esc="closeNavigation"
          >
            <translate i18n-key="LOGOUT" />
          </button>
        </div>
      </div>
      <div
        v-else
        class="portal-sidenavigation__link"
        @click="login"
      >
        <translate i18n-key="LOGIN" />
      </div>
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
          @clickAction="closeNavigation"
          @escButtonClick="closeNavigation"
          @keydown.up.prevent="selectPrevious(index)"
          @keydown.down.prevent="selectNext(index)"
          @keydown.enter.prevent="toggleMenu(index)"
          @keydown.right="focusOnChild(item, index)"
        />
        <template v-if="item.subMenu && item.subMenu.length > 0">
          <menu-item
            v-if="subMenuVisible & (menuParent === index)"
            :title="item.title"
            :is-sub-item="true"
            :links="[]"
            class="portal-sidenavigation__menu-subitem portal-sidenavigation__menu-subitem--parent"
            @click="toggleMenu()"
            @keydown.enter.prevent="toggleMenu()"
          />
          <div
            v-for="(subitem, subindex) in item.subMenu"
            :key="subindex"
            :class="subMenuClass"
          >
            <menu-item
              v-if="subMenuVisible & (menuParent === index)"
              :ref="'subitem' + subindex"
              v-bind="subitem"
              class="portal-sidenavigation__menu-subitem"
              @clickAction="closeNavigation"
            />
          </div>
        </template>
      </div>
    </div>

    <button
      v-if="userState.mayEditPortal"
      class="portal-sidenavigation__link portal-sidenavigation__edit-mode"
      @click="toggleEditMode"
      @keydown.esc="closeNavigation"
    >
      <translate
        v-if="editMode"
        i18n-key="STOP_EDIT_PORTAL"
      />
      <translate
        v-else
        i18n-key="EDIT_PORTAL"
      />
    </button>
  </nav>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import MenuItem from '@/components/navigation/MenuItem.vue';
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
      changeLanguageTranslation: {
        de_DE: 'Sprache ändern',
        en_US: 'change Language',
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
    (this.$refs.loginButton as HTMLElement).focus();
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
    toggleEditMode(): void {
      this.$store.dispatch('portalData/setEditMode', !this.editMode);
      this.closeNavigation();
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
    selectPrevious(index: number):void {
      const currentElementIndex = `menuItem${index}`;
      const currentElement = (this.$refs[currentElementIndex] as HTMLFormElement).$el;
      if (index === 0) {
        // select Last Element
      } else {
        const previousElement = currentElement.parentElement.previousElementSibling.children[0];
        previousElement.focus();
      }
    },
    selectNext(index: number):void {
      const currentElementIndex = `menuItem${index}`;
      const currentElement = (this.$refs[currentElementIndex] as HTMLFormElement).$el;
      if (index === 99) {
        // select Last Element
      } else {
        const nextElement = currentElement.parentElement.nextElementSibling.children[0];
        nextElement.focus();
      }
    },
    hasSubmenu(item) {
      return item.subMenu && item.subMenu.length > 0;
    },
    focusOnChild(item, index) {
      this.toggleMenu(index);
      // const firstClickableChildElement = (this.$refs[`subitem${1}`] as HTMLFormElement).$el;
      // console.log(firstClickableChildElement);
      // firstClickableChildElement.focus();
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
    justify-content: left
    font-size: var(--font-size-normal)
    color: var(--font-color-contrast-high)
    font-weight: 600
    text-transform: uppercase
    background-color: rgba(0,0,0,0)
    border: 0.2rem solid rgba(0,0,0,0)
    &:hover
      background-color: #272726
    &:focus
      border: 0.2rem solid var(--color-primary);
      outline: 0
  &__user-row
    display: flex

    svg
      fill: currentColor
      background-color: var(--color-grey40)
      margin: 0.5rem
      border-radius: 50%
    &> div
      margin: auto 0

  &__logout-link
    text-decoration: underline
    cursor: pointer
    background-color: rgba(0,0,0,0)
    color: var(--font-color-contrast-high)
    font-size: var(--font-size-normal)
    border: 0.2rem solid rgba(0,0,0,0);

    &:hover
      background-color: #272726
    &:focus
      border: 0.2rem solid var(--color-primary);
      outline: 0

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

  &__menu-subitem
    margin-left: 0
    padding: 2rem 0 2rem 2rem;
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
