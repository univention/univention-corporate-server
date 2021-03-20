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
    :tabIndex="tabIndex"
    :class="{ 'header-tab--active': isActive }"
    @click="focusTab"
  >
    <div class="header-tab__background" />

    <image-component
      file-type="svg"
      file-path="./"
      :file-name="logo"
      :alt-text="tabLabel + ' logo'"
    />

    <span
      class="header-tab__title"
      :title="tabLabel"
    >
      {{ tabLabel }}
    </span>

    <header-button
      :icon="closeIcon"
      :aria-label="ariaLabel"
      :no-click="true"
      class="header-tab__close-button"
      @click.stop="closeTab"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import HeaderButton from '@/components/navigation/HeaderButton.vue';
import ImageComponent from '@/components/globals/ImageComponent.vue';

export default defineComponent({
  name: 'HeaderTab',
  components: {
    HeaderButton,
    ImageComponent,
  },
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
  computed: {
    ariaLabel():string {
      return `Close Application: ${this.tabLabel}`;
    },
  },
  methods: {
    focusTab(): void {
      this.$store.dispatch('tabs/setActiveTab', this.tabIndex);
    },
    closeTab(): void {
      this.$store.dispatch('tabs/deleteTab', this.tabIndex);
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
  min-width: calc(30 * var(--layout-spacing-unit));
  height: 50px;
  padding-top: 10px;
  position: relative
  z-index: 1

  &:focus
    --tabColor: var(--color-grey8);
    outline: 0;

  &:hover
    --tabColor: #272726;

  &__background
    transition: background-color 250ms;
    position: absolute;
    top: 10px;
    right: -1px;
    bottom: 0;
    left: -1px;
    border-radius: 8px 8px 0 0;
    background-color: var(--tabColor)
    z-index: -1;

  &__logo
    width: 20px;
    margin: 0 10px;

    &--default
      width: 30px;
      margin: 0 15px;

  &__title
    flex: 1 1 auto;
    width: 20ch;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

  &__close-button
    --button-icon-length: 1.3em;
    margin-left: 0.5em;
    position: relative
    z-index: 10

.header-tab--active
  --tabColor: var(--color-grey8);

  &:focus
    --tabColor: var(--color-grey8);

  &:hover
    --tabColor: var(--color-grey8);
</style>
