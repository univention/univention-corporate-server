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

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'FormCheckMixin',
  data() {
    return {
      error: {},
    };
  },
  computed: {
    ...mapGetters({
      getModalError: 'modal/getModalError',
    }),
  },
  created() {
    // set error object
    const errorObject = {};
    const props = Object.getOwnPropertyNames(this.modelValueData);
    let i = 0;
    for (i; i < props.length; i += 1) {
      errorObject[props[i]] = false;
    }
  },
  methods: {
    checkFormInput() {
      const props = Object.getOwnPropertyNames(this.modelValueData);
      const reqFields = this.requiredFields;

      const modalError = this.getModalError;
      let i = 0;
      for (i; i < props.length; i += 1) {
        // check if we need to test for errors
        if (reqFields.includes(props[i])) {
          if (this.modelValueData[props[i]] === '') {
            this.error[props[i]] = true;

            if (!modalError.includes(`${this.label}_${[props[i]]}`)) {
              this.$store.dispatch('modal/setModalError', `${this.label}_${[props[i]]}`);
            }
          } else {
            this.error[props[i]] = false;
            this.$store.dispatch('modal/removeModalErrorItem', `${this.label}_${[props[i]]}`);
          }
        }
      }
    },
  },
});
</script>

<style>
</style>
