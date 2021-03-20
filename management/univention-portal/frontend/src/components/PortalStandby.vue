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
  <div class="portal-standby">
    <div class="portal-standby__lds-ring">
      <div class="portal-standby__ring-item" />
      <div class="portal-standby__ring-item" />
      <div class="portal-standby__ring-item" />
      <div class="portal-standby__ring-item" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'PortalStandby',
});
</script>

<style lang="stylus" scoped>
.portal-standby
  position: absolute
  top: 0
  left: 0
  background-color: rgba(30, 30, 29, 0.7)
  width: 100%
  height: 100%

  &__lds-ring
    display: inline-block
    position: relative
    width: 80px
    height: 80px
    top: 45%
    left: 45%

  &__ring-item
    box-sizing: border-box
    display: block
    position: absolute
    width: 64px
    height: 64px
    margin: 8px
    border: 8px solid transparent
    border-radius: 50%
    animation: lds-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite
    border-color: var(--color-grey40) transparent transparent transparent

    &:nth-child(1)
      animation-delay: -0.45s

    &:nth-child(2)
      animation-delay: -0.3s

    &:nth-child(3)
      animation-delay: -0.15s

@keyframes lds-ring
  0%
    transform: rotate(0deg)
  100%
    transform: rotate(360deg)
</style>
