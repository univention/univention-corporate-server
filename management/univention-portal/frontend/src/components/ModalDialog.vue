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
    class="dialog"
    @keydown.esc="cancel()"
  >
    <header class="dialog__header">
      <h3>
        <translate
          :i18n-key="i18nTitleKey"
        />
      </h3>
      <icon-button
        v-if="cancelAllowed"
        icon="x"
        @click="cancel()"
      />
    </header>
    <slot />
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import Translate from '@/i18n/Translate.vue';
import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'ModalDialog',
  components: {
    Translate,
    IconButton,
  },
  props: {
    i18nTitleKey: {
      type: String,
      required: true,
    },
    cancelAllowed: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  emits: ['cancel'],
  methods: {
    cancel() {
      if (this.cancelAllowed) {
        this.$emit('cancel');
      }
    },
  },
});
</script>

<style lang="stylus">
.dialog
  padding: calc(2 * var(--layout-spacing-unit)) calc(4 * var(--layout-spacing-unit))
  background: var(--color-grey0)
  border-radius: var(--border-radius-container)
  max-width: calc(50 * var(--layout-spacing-unit))
  box-shadow: var(--box-shadow)

  form
    width: calc(var(--inputfield-width) + 3rem)

  main
    max-height: 26rem
    overflow: auto

  footer
    margin-top: calc(2 * var(--layout-spacing-unit))
    padding-top: calc(2 * var(--layout-spacing-unit))
    border-top: thin solid var(--color-grey8)
    /* padding: var(--layout-spacing-unit-small) calc(2 * var(--layout-spacing-unit))*/
    display: flex
    justify-content: space-between
    flex-wrap: wrap

    button:last-of-type
      margin-left: auto

  &__header
    display: flex
    align-items: center

    button
      margin-left: auto
</style>
