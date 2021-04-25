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
  <div class="portal-modal">
    <modal-wrapper
      :is-active="modalState"
      @backgroundClick="closeModal"
    >
      <component
        :is="modalComponent"
        v-bind="modalProps"
      />
    </modal-wrapper>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import ChangePassword from '@/components/forms/ChangePassword.vue';
import ModalWrapper from '@/components/globals/ModalWrapper.vue';
import PortalFolder from '@/components/PortalFolder.vue';
import ChooseTabs from '@/components/ChooseTabs.vue';
import LoadingOverlay from '@/components/globals/LoadingOverlay.vue';

export default defineComponent({
  name: 'PortalModal',
  components: {
  // Register and import all possible modal components here
  // Otherwise they will not be displyed correctly
  // (Maybe change PortalModal to not use the component tag anymore?)
    ChangePassword,
    ModalWrapper,
    PortalFolder,
    ChooseTabs,
    LoadingOverlay,
  },
  props: {
    isActive: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      modalState: 'modal/getModalState',
      modalComponent: 'modal/getModalComponent',
      modalProps: 'modal/getModalProps',
      modalStubborn: 'modal/getModalStubborn',
    }),
  },
  methods: {
    closeModal(): void {
      if (!this.modalStubborn) {
        this.$store.dispatch('modal/hideAndClearModal');
      }
    },
  },
});
</script>

<style lang="stylus" />
