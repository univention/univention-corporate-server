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
    v-show="isActive"
    class="portal-iframe"
  >
    <span
      class="portal-iframe__status"
    />
    <iframe
      :id="`iframe-${tabId + 1}`"
      ref="iframe"
      :src="link"
      :title="title"
      :tabindex="tabindex"
      class="portal-iframe__iframe"
      allow="geolocation; microphone; camera; midi; encrypted-media"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'PortalIframe',
  props: {
    link: {
      type: String,
      required: true,
    },
    isActive: {
      type: Boolean,
      default: false,
    },
    tabId: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      activeButton: 'navigation/getActiveButton',
    }),
    tabindex(): number {
      return this.activeButton === 'copy' ? -1 : 0;
    },
  },
  mounted() {
    (this.$refs.iframe as HTMLIFrameElement).contentWindow?.focus();
  },
  updated() {
    if (this.isActive && this.activeButton === '') {
      (this.$refs.iframe as HTMLIFrameElement).contentWindow?.focus();
    }
  },
});
</script>

<style lang="stylus">
.portal-iframe
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;

  &__iframe
    position: relative;
    border: none;
    width: 100%;
    height: 100%;

</style>
