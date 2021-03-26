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
    i18n-title-key="CHANGE_PASSWORD"
    @cancel="cancel"
  >
    <form
      @submit.prevent="finish"
    >
      <label>
        <translate i18n-key="OLD_PASSWORD" />
      </label>
      <input
        ref="oldPassword"
        v-model="oldPassword"
        name="old-password"
        type="password"
      >
      <label>
        <translate i18n-key="NEW_PASSWORD" />
      </label>
      <input
        ref="newPassword"
        v-model="newPassword"
        name="new-password"
        type="password"
      >
      <label>
        <translate i18n-key="NEW_PASSWORD" /> (<translate i18n-key="RETYPE" />)
      </label>
      <input
        ref="newPassword2"
        v-model="newPassword2"
        name="new-password-retype"
        type="password"
      >
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          <translate i18n-key="CANCEL" />
        </button>
        <button
          type="submit"
          @click.prevent="finish"
        >
          <translate i18n-key="CHANGE_PASSWORD" />
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import Translate from '@/i18n/Translate.vue';
import ModalDialog from '@/components/ModalDialog.vue';
import { setInvalidity } from '@/jsHelper/tools';

export default defineComponent({
  name: 'ChangePassword',
  components: {
    ModalDialog,
    Translate,
  },
  data() {
    return {
      oldPassword: '',
      newPassword: '',
      newPassword2: '',
    };
  },
  methods: {
    finish() {
      const oldPasswordSet = !!this.oldPassword;
      const newPasswordSet = !!this.newPassword;
      const newPasswordsMatch = this.newPassword === this.newPassword2;
      setInvalidity(this, 'oldPassword', !oldPasswordSet);
      setInvalidity(this, 'newPassword', !newPasswordSet);
      setInvalidity(this, 'newPassword2', !newPasswordsMatch);
      const everythingIsCorrect = oldPasswordSet && newPasswordSet && newPasswordsMatch;
      if (!everythingIsCorrect) {
        return;
      }
      this.$store.dispatch('modal/resolve', {
        oldPassword: this.oldPassword,
        newPassword: this.newPassword,
      });
    },
    cancel() {
      this.$store.dispatch('modal/reject');
    },
  },
});
</script>
