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
          <div
            class="portal-sidenavigation__logout-link"
            @click="logout"
          >
            <translate i18n-key="LOGOUT" />
          </div>
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
        class="portal-sidenavigation__menu-item portal-sidenavigation__menu-item--locale"
        @click="switchLocale"
      >
        <translate i18n-key="SWITCH_LOCALE" />
      </div>
      <div
        v-for="(item, index) in getMenuLinks"
        :key="index"
        :class="setFadeClass()"
        class="portal-sidenavigation__menu-item"
      >
        <menu-item
          v-if="menuVisible"
          :links="[]"
          link-target="samewindow"
          v-bind="item"
          @click="toggleMenu(index)"
          @clickAction="closeNavigation"
        />
        <template v-if="item.subMenu && item.subMenu.length > 0">
          <menu-item
            v-if="subMenuVisible & (menuParent === index)"
            :title="item.title"
            :sub-item="true"
            :links="[]"
            link-target="samewindow"
            class="portal-sidenavigation__menu-subitem portal-sidenavigation__menu-subitem--parent"
            @click="toggleMenu()"
          />
          <div
            v-for="(subitem, subindex) in item.subMenu"
            :key="subindex"
            :class="subMenuClass"
          >
            <menu-item
              v-if="subMenuVisible & (menuParent === index)"
              v-bind="subitem"
              class="portal-sidenavigation__menu-subitem"
              @clickAction="closeNavigation"
            />
          </div>
        </template>
      </div>
    </div>

    <div
      v-if="userState.mayEditPortal"
      class="portal-sidenavigation__link portal-sidenavigation__edit-mode"
      @click="toggleEditMode"
    >
      <translate
        v-if="editMode"
        i18n-key="STOP_EDIT_PORTAL"
      />
      <translate
        v-else
        i18n-key="EDIT_PORTAL"
      />
    </div>
  </nav>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import { mapGetters } from 'vuex';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import MenuItem from '@/components/navigation/MenuItem.vue';

import Translate from '@/i18n/Translate.vue';

@Options({
  name: 'SideNavigation',
  components: {
    PortalIcon,
    MenuItem,
    Translate,
  },
  data() {
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
      getMenuLinks: 'menu/getMenu',
      getLocale: 'locale/getLocale',
      editMode: 'portalData/editMode',
      userState: 'user/userState',
    }),
  },
  methods: {
    switchLocale() {
      if (this.$store.state.locale.locale === 'en_US') {
        this.$store.dispatch('locale/setLocale', { locale: 'de_DE' });
      } else {
        this.$store.dispatch('locale/setLocale', { locale: 'en_US' });
      }
    },
    login() {
      if (this.userState.mayLoginViaSAML) {
        window.location.href = `/univention/saml/?location=${window.location.pathname}`;
      } else {
        window.location.href = `/univention/login/?location=${window.location.pathname}`;
      }
    },
    logout() {
      window.location.href = '/univention/logout';
    },
    closeNavigation() {
      this.$store.dispatch('navigation/setActiveButton', '');
    },
    toggleMenu(index = -1) {
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
    toggleEditMode() {
      this.$store.dispatch('portalData/setEditMode', !this.editMode);
      this.closeNavigation();
    },
    setFadeClass() {
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
  },
})

export default class SideNavigation extends Vue {}
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
    &:hover
      background-color: #272726

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
    &:hover
      background-color: #272726

  &__login-header
    border-bottom: 4px solid var(--color-grey8)

  &__menu
    margin: 0
    margin-bottom: auto
    padding-left: 0

  &__menu-item
    margin-left: 0

    &--locale
      padding: 2rem 0 2rem 2rem;
      &:hover
        background-color: #272726
        cursor: pointer

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
