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
  <tabindex-element
    :id="`headerTab__${idx}`"
    :ref="`headerTab__${idx}`"
    tag="div"
    :active-at="['portal']"
    :hidden="hidden"
    class="header-tab"
    :class="{ 'header-tab--active': isActive }"
    @click="focusTab"
    @keydown.enter="focusTab"
  >
    <div
      ref="tabFocusWrapper"
      class="header-tab__focus-wrapper"
      :aria-label="ariaLabelFocus"
      @blur="removeFocusStyleFromParent()"
    >
      <!-- Alt-Tag should be empty, since it's not necessary for screenreader users -->
      <div
        class="header-tab__logo-wrapper"
        :style="backgroundColor ? `background: ${backgroundColor}` : ''"
      >
        <img
          :src="logo"
          onerror="this.src='./questionMark.svg'"
          alt=""
          class="header-tab__logo"
        >
      </div>
      <span
        class="header-tab__title"
        :title="tabLabel"
      >
        {{ tabLabel }}
      </span>
    </div>
    <icon-button
      :id="`close-tab-${idx}`"
      icon="x"
      :aria-label-prop="ariaLabelClose"
      class="header-tab__close-button"
      :hidden="hidden"
      @click="closeTab"
    />
  </tabindex-element>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import TabindexElement from '@/components/activity/TabindexElement.vue';
import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'HeaderTab',
  components: {
    IconButton,
    TabindexElement,
  },
  props: {
    idx: {
      type: Number,
      required: true,
    },
    backgroundColor: {
      type: String,
      default: '',
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
    hidden: {
      type: Boolean,
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
    ariaLabelClose(): string {
      return `${this.tabLabel}:  ${this.$translateLabel('CLOSE_TAB')}`;
    },
    ariaLabelFocus(): string {
      return `${this.tabLabel}:  ${this.$translateLabel('SELECT_TAB')}`;
    },
  },
  mounted() {
    this.isMounted = true;
  },
  methods: {
    focusTab(): void {
      this.$store.dispatch('tabs/setActiveTab', this.idx);
    },
    closeTab(): void {
      this.$store.dispatch('tabs/deleteTab', this.idx);
    },
  },
});
</script>

<style lang="stylus">
.header-tab
  outline: 0
  cursor: pointer
  display: flex
  align-items: center
  position: relative
  z-index: 1
  background-color: transparent
  transition: background-color var(--portal-transition-duration)
  flex-basis: auto
  flex-grow: 1
  max-width: 15rem
  border: 0.2rem solid rgba(0,0,0,0)

  &__logo-wrapper
    background-color: var(--bgc-apptile-default)
    border-radius: var(--border-radius-apptile)
    height: calc(var(--portal-header-height) * 0.8)
    width: @height
    display: flex
    align-items: center
    justify-content: center
    margin: 0 var(--layout-spacing-unit-small)

  &__logo
    width: 80%
    max-height: 80%
    vertical-align: middle
    border: 0

  &__title
    flex: 1 1 auto
    overflow: hidden
    text-overflow: ellipsis
    white-space: nowrap
    min-width: 2.5rem

  &__close-button
    position: relative
    z-index: 10

  &__focus-wrapper
    display: flex
    align-items: center
    min-width: 40px
    width: 100%

  &:focus
    border-color: var(--color-focus)

  &--active
    background-color: var(--portal-tab-background)
</style>
