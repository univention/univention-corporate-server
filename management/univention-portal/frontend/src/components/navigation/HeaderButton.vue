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
  >
    <span
      :class="'header-button__inner'"
      role="presentation"
    >
      <button
        :ref="setRef"
        :aria-expanded="isActiveButton"
        :aria-label="ariaLabel"
        :class="['header-button__button', hoverClass]"
      >
        <portal-icon
          :icon="icon"
          icon-width="2rem"
        />
      </button>
    </span>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'HeaderButton',
  components: {
    PortalIcon,
  },
  props: {
    icon: {
      type: String,
      required: true,
    },
    ariaLabel: {
      type: String,
      required: true,
    },
    noClick: {
      type: Boolean,
      default: false,
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
  },
});
</script>

<style lang="stylus">
.header-button
  --font-size-button-icon: var(--font-size-big)
  margin: 0 var(--layout-spacing-unit-small)
  --bgc: transparent
  --bgc-state: transparent
  box-shadow: none
  border-radius: var(--button-icon-border-radius)

  &--is-active
      z-index:1000

      svg
        color: var(--color-primary)

  &__inner
    border: none
    border-radius: inherit
    display: flex
    align-items: center
    justify-content: center
    transition: var(--button-bgc-transition)
    background-color: var(--bgc-state)
    transition: opacity 250ms
    font-size: var(--button-font-size)

  &__button
    width: 4rem
    height: 4rem
    background: none
    border: none
    color: white
    display: flex
    align-items: center
    justify-content: center
    background-color: transparent
    border: 0.2rem solid rgba(0,0,0,0)

    &:hover,
    &:focus
      border-radius: 100%
    &:focus
      border: 0.2rem solid var(--color-primary)
      outline: none

    &--success
      &:hover,
      &:focus
        background-color: var(--notification-success)

    &--warning
      &:hover,
      &:focus
        background-color: var(--notification-warning)

    &--error
      &:hover,
      &:focus
        background-color: var(--notification-error)

    &:hover
      cursor: pointer
</style>
