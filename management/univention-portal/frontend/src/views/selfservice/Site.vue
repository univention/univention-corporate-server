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
  <modal-wrapper
    :is-active="initialLoadDone"
    :full="true"
    class="modal-wrapper--selfservice"
  >
    <modal-dialog
      ref="dialog"
      :i18n-title-key="title"
      modal-level="selfservice"
      class="dialog--selfservice"
      @cancel="cancel"
    >
      <template
        v-if="subtitle"
        #description
      >
        {{ subtitle }}
      </template>
      <div>
        <slot />
      </div>
    </modal-dialog>
  </modal-wrapper>
</template>

<script lang="ts">
// FIXME if using 'initialLoadDone' for is-active there are weird z-indexing css issues with the opacity animation
import { defineComponent } from 'vue';

import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'Site',
  components: {
    ModalDialog,
    ModalWrapper,
  },
  props: {
    title: {
      type: String,
      required: true,
    },
    subtitle: {
      type: String,
      default: '',
    },
  },
  computed: {
    ...mapGetters({
      metaData: 'metaData/getMeta',
      initialLoadDone: 'getInitialLoadDone',
    }),
  },
  mounted() {
    this.$store.dispatch('activity/setLevel', 'selfservice');
    document.body.classList.add('body--has-selfservice');
  },
  unmounted() {
    this.$store.dispatch('activity/setLevel', 'portal');
    document.body.classList.remove('body--has-selfservice');
  },
  methods: {
    cancel() {
      this.$router.push({ name: 'portal' });
    },
  },
});
</script>

<style lang="stylus">
body.body--has-selfservice
  overflow: hidden

.modal-wrapper--selfservice
  padding: calc(4 * var(--layout-spacing-unit)) 0
  overflow: auto
  box-sizing: border-box
  &.modal-wrapper--isVisible
    // z-index: $zindex-4 TODO notifications are also $zindex-4
    z-index: 399

.dialog--selfservice
  margin: auto
  box-sizing: border-box
  min-width: s('min(calc(var(--inputfield-width) + calc(12 * var(--layout-spacing-unit))), 90%)')
  min-height: s('min(200px, 90%)')
  max-height: unset

  input,
  select,
  form
    width: 100%

  form main
    max-height: unset
    padding: 0
</style>
