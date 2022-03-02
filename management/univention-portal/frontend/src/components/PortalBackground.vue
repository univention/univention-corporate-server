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
    class="portal__background"
    :style="backgroundImageStyle"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'PortalBackground',
  computed: {
    ...mapGetters({ portal: 'portalData/getPortal' }),
    backgroundImageStyle(): string {
      if (!this.portal.portal.background) {
        return 'background-image: none';
      }
      return `background-image: url('${this.portal.portal.background}')`;
    },
  },
});
</script>

<style lang="stylus">
.portal__background {
  position: fixed;
  z-index: $zindex-0;
  top: var(--portal-header-height);
  left: 0;
  right: 0;
  bottom: 0;
  background-position: top center;
  background-size: cover;
  background-repeat: no-repeat;
}
</style>
