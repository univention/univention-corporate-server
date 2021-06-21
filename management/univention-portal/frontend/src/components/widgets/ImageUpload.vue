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
  <div class="image-upload">
    <label>{{ label }}</label>
    <div
      class="image-upload__canvas"
      @dragenter.prevent=""
      @dragover.prevent=""
      @drop.prevent="drop"
      @click="startUpload"
    >
      <img
        v-if="modelValue"
        :src="modelValue"
        alt=""
      >
      <div
        v-else
        class="image-upload__nofile"
      >
        <translate
          i18n-key="SELECT_FILE"
        />
      </div>
    </div>
    <footer class="image-upload__footer">
      <input
        ref="file_input"
        class="image-upload__file-input"
        type="file"
        @change="upload"
      >
      <button
        type="button"
        @click.prevent="startUpload"
      >
        <portal-icon
          icon="upload"
        />
        <translate
          i18n-key="UPLOAD"
        />
      </button>
      <button
        type="button"
        @click.prevent="remove"
      >
        <portal-icon
          icon="trash"
        />
        <translate
          i18n-key="REMOVE"
        />
      </button>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'ImageUpload',
  components: {
    PortalIcon,
    Translate,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    modelValue: {
      type: String,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  methods: {
    drop(evt: DragEvent) {
      const dt = evt.dataTransfer;
      if (dt && dt.files) {
        this.handleFiles(dt.files);
      }
    },
    startUpload() {
      (this.$refs.file_input as HTMLElement).click();
    },
    upload(evt: Event) {
      const target = evt.target as HTMLInputElement;
      if (target.files) {
        this.handleFiles(target.files);
      }
    },
    handleFiles(files) {
      const file = files[0];
      const reader = new FileReader();

      reader.onload = (e) => {
        if (e.target) {
          console.log('e.target: ', e.target);
          this.$emit('update:modelValue', e.target.result);
        }
      };
      reader.readAsDataURL(file);
    },
    remove() {
      this.$emit('update:modelValue', '');
    },
  },
});
</script>

<style lang="stylus">
.image-upload
  &__canvas
    height: 10rem
    width: 10rem
    cursor: pointer
    display: flex
    background: repeating-conic-gradient(var(--bgc-apptile-default) 0% 25%, transparent 0% 50%) 50% / 20px 20px
    img
      max-height: 10rem
      margin: auto
  &__footer
    margin: var(--layout-spacing-unit) 0
    display: flex
    button + button
      margin-left: var(--layout-spacing-unit)
  &__file-input
    visibility: hidden
    position: absolute
  &__nofile
    height: 100%
    width: 100%
    display: flex
    background-color: var(--bgc-content-body)
    span
      margin: auto
</style>
