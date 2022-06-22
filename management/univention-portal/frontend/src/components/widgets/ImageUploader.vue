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
    :class="[
      'image-upload',
      {
        'image-upload--loading': loading
      }
    ]"
  >
    <div
      class="image-upload__canvas"
      :data-test="`imageUploadCanvas--${extraLabel}`"
      @dragenter.prevent=""
      @dragover.prevent=""
      @drop.prevent="drop"
      @click="triggerUpload"
    >
      <img
        v-if="modelValue"
        :src="modelValue"
        :data-test="`imagePreview--${extraLabel}`"
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
      <Transition name="loading">
        <standby-wrapper
          v-if="loading"
          class="image-upload__standby"
        />
      </Transition>
    </div>
    <div class="image-upload__maxFileSize">
      {{ UPLOAD_MAX }}
    </div>
    <footer class="image-upload__footer">
      <input
        ref="fileInput"
        class="image-upload__file-input"
        type="file"
        :data-test="`imageUploadFileInput--${extraLabel}`"
        :accept="accept"
        @change="onUpload"
      >
      <button
        ref="uploadButton"
        type="button"
        :tabindex="tabindex"
        :data-test="`imageUploadButton--${extraLabel}`"
        @click.prevent="triggerUpload"
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
        :data-test="`imageRemoveButton--${extraLabel}`"
        @click.prevent="remove"
      >
        <portal-icon
          icon="trash"
        />
        {{ REMOVE }}
        <span class="sr-only sr-only-mobile">
          {{ extraLabel }}
        </span>
      </button>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import StandbyWrapper from '@/components/StandbyWrapper.vue';
import { mapGetters } from 'vuex';

interface ImageUploadData {
  fileName: string,
  loading: boolean,
  maxFileSize: number,
}

export default defineComponent({
  name: 'ImageUploader',
  components: {
    PortalIcon,
    StandbyWrapper,
  },
  props: {
    extraLabel: {
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
    forAttrOfLabel: {
      type: String,
      required: true,
    },
    invalidMessageId: {
      type: String,
      required: true,
    },
    // defines the 'accept' attribute of the <input type=file> node
    // valid values are:
    // A valid case-insensitive filename extension, starting with a period (".") character. For example: .jpg, .pdf, or .doc.
    // A valid MIME type string, with no extensions.
    // The string audio/* meaning "any audio file".
    // The string video/* meaning "any video file".
    // The string image/* meaning "any image file".
    accept: {
      type: String,
      default: 'image/*',
    },
  },
  emits: ['update:modelValue'],
  data(): ImageUploadData {
    return {
      fileName: '',
      loading: false,
      maxFileSize: 2048 * 1024, // 2048 kibibytes
    };
  },
  computed: {
    ...mapGetters({
      metaData: 'metaData/getMeta',
    }),
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
      return `${this.extraLabel}, ${this.hasImage}`;
    },
    UPLOAD_MAX(): string {
      // show maxFileSize in MiB (Mebibyte - 1024² bytes)
      return _('(maximum file size is %(maxFileSize)s MB)', {
        maxFileSize: (this.maxFileSize / (1024 * 1024)).toFixed(1).toString(),
      });
    },
    hasImage(): string {
      return this.modelValue ? this.fileName : _('no file selected');
    },
  },
  created() {
    const uploadMax = parseInt(this.metaData['umc/server/upload/max'], 10);
    if (Number.isNaN(uploadMax)) {
      console.warn(`The value of the ucr variable "umc/server/upload/max" (${this.metaData['umc/server/upload/max']}) can't be converted to a number. Using default of ${(this.maxFileSize / 1024).toFixed(1)} KiB.`);
    } else {
      // 'umc/server/upload/max' is in kibibytes; we want bytes
      this.maxFileSize = uploadMax * 1024;
    }
  },
  methods: {
    triggerUpload() {
      (this.$refs.fileInput as HTMLElement).click();
    },
    drop(evt: DragEvent) {
      const dt = evt.dataTransfer;
      if (dt && dt.files && dt.files.length) {
        this.setFile(dt.files[0]);
      }
    },
    onUpload(evt: Event) {
      const target = evt.target as HTMLInputElement;
      if (target.files && target.files.length) {
        this.setFile(target.files[0]);
      }
    },
    setFile(file) {
      const fileInputNode = this.$refs.fileInput as HTMLInputElement;

      // validate max file size
      if (file.size > this.maxFileSize) {
        fileInputNode.value = '';
        this.$store.dispatch('notifications/addErrorNotification', {
          title: '',
          description: _('The image "%(filename)s" could not be uploaded because it exceeds the maximum file size of %(maxFileSize)s MB.', {
            filename: file.name,
            // show maxFileSize in MiB (Mebibyte - 1024² bytes)
            maxFileSize: (this.maxFileSize / (1024 * 1024)).toFixed(1).toString(),
          }),
        });
        return;
      }

      // validate file type
      const accepted = this.accept?.split(',').map((type) => type.trim());
      if (accepted) {
        const valid = accepted.some((accept) => {
          if (accept.startsWith('.')) {
            const fileExtension = file.name
              .split('.')
              .pop()
              .toLowerCase();
            return `.${fileExtension}` === accept.toLowerCase();
          }
          if (['image/*', 'audio/*', 'video/*'].includes(accept)) {
            const acceptStart = accept.split('*')[0];
            return file.type.startsWith(acceptStart);
          }
          return file.type === accept;
        });

        if (!valid) {
          fileInputNode.value = '';
          this.$store.dispatch('notifications/addErrorNotification', {
            title: '',
            description: _('The file "%(filename)s" could not be uploaded because it is an unaccepted file type.', {
              filename: file.name,
            }),
          });
          return;
        }
      }

      this.loading = true;
      this.fileName = file.name;
      const reader = new FileReader();
      reader.onload = (e) => {
        this.loading = false;
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
    focus() {
      (this.$refs.uploadButton as HTMLButtonElement).focus();
    },
  },
});
</script>

<style lang="stylus">
.image-upload
  &__canvas
    position: relative
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
  &__maxFileSize
    color: var(--font-color-contrast-middle)
    font-size: var(--font-size-5)
    padding-top: var(--layout-spacing-unit-small)

.image-upload__standby
  position: absolute
  top: 0
  left: 0
  background: var(--bgc-inputfield-on-container)

.loading-enter-active,
.loading-leave-active {
  transition: opacity 0.5s ease;
}

.loading-enter-from,
.loading-leave-to {
  opacity: 0;
}
</style>
