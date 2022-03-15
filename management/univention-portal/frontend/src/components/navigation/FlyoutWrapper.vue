<!--
Copyright 2021-2022 Univention GmbH

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
    :class="{ 'flyout-wrapper--isVisible': isVisible }"
    class="flyout-wrapper"
  >
    <slot />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'FlyoutWrapper',
  props: {
    isVisible: {
      type: Boolean,
      required: true,
    },
  },
});
</script>

<style lang="stylus">
.flyout-wrapper
  width: 100%
  max-width: 23rem
  position: fixed
  top:  calc(var(--portal-header-height) + var(--layout-spacing-unit))
  bottom: env(safe-area-inset-bottom, 0)
  right: 0
  z-index: 100
  background-color: var(--bgc-content-container)
  transform: translate3d(110%, 0, 0)
  transition: transform cubic-bezier(0, 0, 0.2, 1) 0.5s

  &--isVisible
    transform: translate3d(0, 0, 0) scale(1, 1)
    transition: transform cubic-bezier(0, 0, 0.2, 1) 0.5s
</style>
