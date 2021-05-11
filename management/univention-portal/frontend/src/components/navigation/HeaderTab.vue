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
  <div
    :id="`headerTab__${tabIndex}`"
    :ref="`headerTab__${tabIndex}`"
    class="header-tab"
    :class="{ 'header-tab--active': isActive, 'header-tab--focus': hasFocus }"
    @click="focusTab"
  >
    <div
      ref="tabFocusWrapper"
      class="header-tab__focus-wrapper"
      tabIndex="0"
      :aria-label="ariaLabelFocus"
      @keydown.enter="focusTab('setFocusOnIframe')"
      @focus="setFocusStyleToParent()"
      @blur="removeFocusStyleFromParent()"
    >
      <!-- Alt-Tag should be empty, since it's not necessary for screenreader users -->
      <img
        :src="logo"
        onerror="this.src='./questionMark.svg'"
        alt=""
        class="header-tab__logo"
      >
      <span
        class="header-tab__title"
        :title="tabLabel"
      >
        {{ tabLabel }}
      </span>
    </div>
    <header-button
      :icon="closeIcon"
      :aria-label="ariaLabelClose"
      :no-click="true"
      class="header-tab__close-button"
      @click.stop="closeTab"
      @keydown.enter.prevent="reManageFocus"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import HeaderButton from '@/components/navigation/HeaderButton.vue';

export default defineComponent({
  name: 'HeaderTab',
  components: { HeaderButton },
  props: {
    tabIndex: {
      type: Number,
      required: true,
    },
    tabLabel: {
      type: String,
      default: 'Nav Tab',
    },
    closeIcon: {
      type: String,
      default: 'x',
    },
    isActive: {
      type: Boolean,
      default: false,
    },
    logo: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      isMounted: false,
      hasFocus: false,
    };
  },
  computed: {
    ariaLabelClose():string {
      // TODO Screenreader Translations
      return ` ${this.tabLabel}: Close Tab.`;
    },
    ariaLabelFocus():string {
      // TODO Screenreader Translations
      return ` ${this.tabLabel}: To Focus press Enter`;
    },
  },
  mounted() {
    this.isMounted = true;
  },
  methods: {
    focusTab(): void {
      this.$store.dispatch('tabs/setActiveTab', this.tabIndex);
    },
    closeTab(): void {
      this.$store.dispatch('tabs/deleteTab', this.tabIndex);
    },
    setFocusStyleToParent():void {
      this.hasFocus = true;
    },
    removeFocusStyleFromParent():void {
      this.hasFocus = false;
    },
    reManageFocus():void {
      this.closeTab();
    },
  },
});
</script>

<style lang="stylus">
.header-tab
  --tabColor: transparent;
  outline: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  position: relative
  z-index: 1
  background-color: var(--tabColor)
  transition: background-color 250ms;
  flex-basis: auto;
  flex-grow: 1;
  max-width: 15rem;
  border: 0.2rem solid rgba(0,0,0,0)

  &:focus
    --tabColor: var(--color-grey8);
    outline: 0;

  &:hover
    --tabColor: #272726;

  &__logo
    width: 20px;
    margin: 0 10px;

    &--default
      width: 30px;
      margin: 0 15px;

  &__title
    flex: 1 1 auto;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 2.5rem;

  &__close-button
    position: relative
    z-index: 10

  &__focus-wrapper
    display: flex
    align-items: center
    min-width: 40px
    width: 100%

  &--focus
    border-color: var(--color-focus);

  &--active
    --tabColor: var(--color-grey8);

    &:focus
      --tabColor: var(--color-grey8);

    &:hover
      --tabColor: var(--color-grey8);
</style>
