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
    v-if="showTooltip"
    class="portal-tooltip"
    :class="{'portal-tooltip--shown': isDisplayed}"
    role="tooltip"
  >
    <div class="portal-tooltip__header">
      <div class="portal-tooltip__thumbnail">
        <img
          :src="icon || './questionMark.svg'"
          onerror="this.src='./questionMark.svg'"
          :alt="`${title} logo`"
          class="portal-tooltip__logo"
        >
      </div>
      <div class="portal-tooltip__title">
        {{ title }}
      </div>
    </div>

    <!-- eslint-disable vue/no-v-html -->
    <div
      v-if="description"
      :id="ariaId"
      class="portal-tooltip__description"
      v-html="description"
    />
    <!-- eslint-enable vue/no-v-html -->
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'PortalToolTip',
  props: {
    title: {
      type: String,
      default: '',
    },
    icon: {
      type: String,
      default: '', // TODO: add fallback icon
    },
    description: {
      type: String,
      default: '',
    },
    link: {
      type: String,
      default: '',
    },
    ariaId: {
      type: String,
      default: '',
    },
    isDisplayed: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    showTooltip(): boolean {
      let ret = true;
      if (
        (this.icon === '') ||
        (this.title === '') ||
        (this.description === '')
      ) {
        ret = false;
      }
      return ret;
    },
  },
});
</script>

<style scoped lang="stylus">
.portal-tooltip
  font-size: 16px // 0.8rem
  position: fixed
  bottom: calc(2 * 1rem)
  right: calc(2 * 1rem)
  background-color: #1e1e1d
  border-radius: 16px
  min-width: calc(20 * 1rem)
  max-width: calc(40 * 1rem)
  padding: calc(2 * 1rem)
  box-shadow: 0rem 0.3rem 0.6rem rgba(0, 0, 0, 0.16)
  pointer-events: none
  z-index: $zindex-3
  color: var(--color-white)
  display: none;

  &--shown {
    display: block;
  }
  &__header
    display: flex
    align-items: center
    margin-bottom: calc(2 * 1rem)

  &__thumbnail
    border-radius: 15%
    display: flex
    align-items: center
    justify-content: center
    box-shadow: 0 0.3rem 0.6rem rgba(0, 0, 0, 0.16)
    background: #868681

    .portal-tooltip__header &
      width: calc(3 * 1rem)
      height: calc(3 * 1rem)
      margin-right: calc(3 * calc(1rem / 2))

  &__logo
    width: 80%
    vertical-align: middle
    border: 0
</style>
