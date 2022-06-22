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
  <input
    :id="forAttrOfLabel"
    ref="input"
    type="number"
    :name="name"
    :value="modelValue"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId || null"
    data-test="number-spinner"
    @input="$emit('update:modelValue', $event.target.value)"
  >
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'NumberSpinner',
  props: {
    name: {
      type: String,
      required: true,
    },
    modelValue: {
      type: String,
      required: true,
    },
    invalidMessage: {
      type: String,
      default: '',
    },
    forAttrOfLabel: {
      type: String,
      required: true,
    },
    invalidMessageId: {
      type: String,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'NumberSpinner',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus() {
      (this.$refs.input as HTMLInputElement).focus();
    },
  },
});

</script>
