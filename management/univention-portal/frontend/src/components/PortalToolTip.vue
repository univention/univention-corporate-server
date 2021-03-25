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
    class="portal-tooltip"
    role="tooltip"
  >
    <div
      class="portal-tooltip__header"
      data-test="portal-tooltip"
    >
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
    ariaId: {
      type: String,
      default: '',
    },
  },
});
</script>

<style scoped lang="stylus">
.portal-tooltip
  position: fixed
  bottom: 1rem
  right: 1rem
  background-color: #1e1e1d
  border-radius: var(--border-radius-tooltip)
  min-width: calc(20 * 1rem)
  max-width: calc(20 * 1rem)
  padding: 1rem
  box-shadow: var(--box-shadow)
  pointer-events: none
  z-index: $zindex-3
  color: var(--color-white)
  display: block;

  &__header
    display: flex
    align-items: center
    margin-bottom: 1rem

  &__thumbnail
    border-radius: var(--border-radius-apptile)
    display: flex
    align-items: center
    justify-content: center
    box-shadow: 0 0.3rem 0.6rem rgba(0, 0, 0, 0.16)
    background: var(--color-grey40)

    .portal-tooltip__header &
      width: calc(3 * 1rem)
      height: calc(3 * 1rem)
      margin-right: calc(3 * calc(1rem / 2))

  &__logo
    width: 80%
    vertical-align: middle
    border: 0
</style>
