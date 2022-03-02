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
  <div class="image-upload">
    <label>{{ label }}</label>
    <div
      class="image-upload__canvas"
      :data-test="`imageUploadCanvas--${label}`"
      @dragenter.prevent=""
      @dragover.prevent=""
      @drop.prevent="drop"
      @click="startUpload"
    >
      <img
        v-if="modelValue"
        :src="modelValue"
        :data-test="`imagePreview--${label}`"
        alt=""
      >
      <div
        v-else
        class="image-upload__nofile"
      >
        <span>
          {{ SELECT_FILE }}
        </span>
      </div>
    </div>
    <footer class="image-upload__footer">
      <input
        ref="file_input"
        class="image-upload__file-input"
        type="file"
        :data-test="`imageUploadFileInput--${label}`"
        @change="upload"
      >
      <button
        type="button"
        :tabindex="tabindex"
        :data-test="`imageUploadButton--${label}`"
        @click.prevent="startUpload"
      >
        <portal-icon
          icon="upload"
        />
        {{ UPLOAD }}
        <span class="sr-only sr-only-mobile">
          {{ IMAGE_UPLOAD_STATE }}
        </span>
      </button>
      <button
        type="button"
        :tabindex="tabindex"
        :disabled="!modelValue"
        :data-test="`imageRemoveButton--${label}`"
        @click.prevent="remove"
      >
        <portal-icon
          icon="trash"
        />
        {{ REMOVE }}
        <span class="sr-only sr-only-mobile">
          {{ label }}
        </span>
      </button>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import PortalIcon from '@/components/globals/PortalIcon.vue';

interface ImageUploadData {
  fileName: string,
}

export default defineComponent({
  name: 'ImageUpload',
  components: {
    PortalIcon,
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
    tabindex: {
      type: Number,
      default: 0,
    },
  },
  emits: ['update:modelValue'],
  data(): ImageUploadData {
    return {
      fileName: '',
    };
  },
  computed: {
    SELECT_FILE(): string {
      return _('Select file');
    },
    UPLOAD(): string {
      return _('Upload');
    },
    REMOVE(): string {
      return _('Remove');
    },
    IMAGE_UPLOAD_STATE(): string {
      return `${this.label}, ${this.hasImage}`;
    },
    hasImage(): string {
      return this.modelValue ? this.fileName : _('no file selected');
    },
  },
  methods: {
    drop(evt: DragEvent) {
      const dt = evt.dataTransfer;
      if (dt && dt.files) {
        this.handleFile(dt.files);
      }
    },
    startUpload() {
      (this.$refs.file_input as HTMLElement).click();
    },
    upload(evt: Event) {
      const target = evt.target as HTMLInputElement;
      if (target.files) {
        this.fileName = target.files[0].name;
        this.handleFile(target.files[0]);
      }
    },
    handleFile(file) {
      // const file = files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target) {
          this.$emit('update:modelValue', e.target.result);
        }
      };
      reader.readAsDataURL(file);
    },
    remove() {
      this.$emit('update:modelValue', '');
      this.fileName = '';
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
    background: var(--bgc-checkerboard)
    img
      max-height: 10rem
      margin: auto
      max-width: 100%
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
    background-color: var(--bgc-inputfield-on-container)
    span
      margin: auto
</style>
