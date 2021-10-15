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
  <modal-dialog
    :title="REMOVE"
    :modal-level="modalLevel"
    @cancel="cancel"
  >
    <form class="confirm-dialog">
      <div class="confirm-dialog__content">
        {{ CONFIRM }}
      </div>
      <footer class="confirm-dialog__footer">
        <button
          ref="cancel"
          type="submit"
          class="primary"
          @click.prevent="cancel"
        >
          {{ CANCEL }}
        </button>
        <button
          type="button"
          @click.prevent="finish('remove')"
        >
          {{ DELETE }}
        </button>
        <button
          type="button"
          @click.prevent="finish('unlink')"
        >
          {{ REMOVE }}
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import Region from '@/components/activity/Region.vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';

export default defineComponent({
  name: 'ConfirmDialog',
  components: {
    ModalDialog,
    ModalWrapper,
    Region,
  },
  props: {
    title: {
      type: String,
      default: 'REMOVE',
    },
  },
  computed: {
    CONFIRM(): string {
      return _('Do you really want to remove this object? You can completely delete it, or just remove the link to the object here, so that you can still use it somewhere else.');
    },
    CANCEL(): string {
      return _('Cancel');
    },
    DELETE(): string {
      return _('Delete');
    },
    REMOVE(): string {
      return _('Remove');
    },
    modalLevel(): string {
      // Modal 2 Because it set the correct tabindizies for elements in modal Level 1
      return 'modal2';
    },
  },
  mounted(): void {
    (this.$refs.cancel as HTMLElement).focus();
  },
  methods: {
    cancel(): void {
      this.$store.dispatch('modal/reject', 2);
    },
    finish(action: string): void {
      this.$store.dispatch('modal/resolve', {
        level: 2, // Will be displayed in second Level Modal
        action,
      });
    },
  },
});
</script>

<style lang="stylus">
form.confirm-dialog
  width: calc(var(--inputfield-width) + 5rem)

  footer.confirm-dialog__footer:not(.image-upload__footer):not(.multi-select__footer) button:last-of-type
    margin-left: inherit
</style>
