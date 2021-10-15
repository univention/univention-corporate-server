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
    :class="{ 'header-button--is-active': isActiveButton }"
    class="header-button"
    @click="toggleActiveButton"
    @keyup.esc.stop="emptyActiveButton"
  >
    <div
      :class="'header-button__inner'"
      role="presentation"
    >
      <tabindex-element
        :id="'header-button-' + icon"
        :ref="setRef"
        tag="button"
        :active-at="['portal', `header-${icon}`]"
        :aria-expanded="isActiveButton"
        :aria-label="ariaLabel"
        :class="['header-button__button', hoverClass]"
      >
        <portal-icon
          :icon="icon"
        />
        <div
          v-if="counter"
          class="header-button__detail"
        >
          {{ counter }}
        </div>
      </tabindex-element>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import TabindexElement from '@/components/activity/TabindexElement.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'HeaderButton',
  components: {
    PortalIcon,
    TabindexElement,
  },
  props: {
    icon: {
      type: String,
      required: true,
    },
    ariaLabelProp: {
      type: String,
      required: true,
    },
    noClick: {
      type: Boolean,
      default: false,
    },
    counter: {
      type: Number,
      default: null,
    },
    hoverClass: {
      type: String,
      default: '',
    },
  },
  computed: {
    isActiveButton(): boolean {
      return this.$store.state.navigation.activeButton === this.icon;
    },
    setRef(): string {
      return `${this.icon}Reference`;
    },
    ariaLabel(): string {
      let ariaLabel = '';
      if (this.counter === null) {
        ariaLabel = this.ariaLabelProp;
      } else if (this.counter === 1) {
        ariaLabel = `${this.ariaLabelProp}: ${this.counter} ${_('item')}`;
      } else {
        ariaLabel = `${this.ariaLabelProp}: ${this.counter} ${_('items')}`;
      }
      return ariaLabel;
    },
  },
  methods: {
    toggleActiveButton(): void {
      if (!this.noClick) {
        if (this.isActiveButton) {
          this.$store.dispatch('navigation/setActiveButton', '');
        } else {
          this.$store.dispatch('navigation/setActiveButton', this.icon);
        }
      }
    },
    emptyActiveButton(): void {
      if (!this.noClick) {
        this.$store.dispatch('navigation/setActiveButton', '');
      }
    },
  },
});
</script>

<style lang="stylus">
.header-button
  --font-size-button-icon: var(--font-size-2)
  margin: 0 var(--layout-spacing-unit-small)
  --bgc: transparent
  --bgc-state: transparent
  box-shadow: none
  border-radius: var(--button-icon-border-radius)
  height: calc(4.5 * var(--layout-spacing-unit))
  width: @height

  &--is-active
      z-index:1000

      svg
        color: var(--color-accent)

  &__inner
    border: none
    border-radius: inherit
    display: flex
    align-items: center
    justify-content: center
    transition: var(--button-bgc-transition)
    background-color: var(--bgc-state)
    transition: opacity var(--portal-transition-duration)
    font-size: var(--button-font-size)
    width: inherit
    height: inherit

  &__button
    position: relative
    font-size: var(--font-size-3)
    background: none
    border: none
    color: white
    display: flex
    align-items: center
    justify-content: center
    background-color: transparent
    border: 0.2rem solid rgba(0,0,0,0)
    padding: var(--layout-spacing-unit)
    width: inherit
    height: inherit
    border-radius: var(--border-radius-circles)

    &:hover,
    &:focus
      border-radius: 100%
    &:focus
      border: 0.2rem solid var(--color-focus)
      outline: none

    &:hover
      cursor: pointer

  &__detail
    position: absolute
    color: var(--bgc-content-header)
    background-color: var(--bgc-header-number-circle)
    font-size: var(--font-size-5)
    width: 1.6em
    height: 1.6em
    left: 2em
    top: -0.5em
    border-radius: var(--border-radius-circles)
    display: flex
    align-items: center
    justify-content: center
    pointer-events: none

#header-button-bell svg
#header-button-copy svg
  margin-right: 0!important
</style>
