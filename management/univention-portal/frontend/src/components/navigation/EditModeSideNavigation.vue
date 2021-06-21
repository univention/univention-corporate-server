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
  <nav class="portal-sidenavigation">
    <form
      class="edit-mode-side-navigation__form"
      @submit.prevent="saveChanges"
    >
      <image-upload
        v-model="portalLogoData"
        :label="$translateLabel('PORTAL_LOGO')"
      />
      <locale-input
        v-model="portalNameData"
        i18n-label="NAME"
        name="name"
        @update:modelValue="update"
      />
      <image-upload
        v-model="portalBackgroundData"
        :label="$translateLabel('BACKGROUND')"
      />
      <label>
        <translate i18n-key="DEFAULT_LINK_TARGET" />
        <select
          v-model="portalDefaultLinkTargetData"
        >
          <option value="samewindow">{{ $translateLabel('SAME_WINDOW') }}</option>
          <option value="newwindow">{{ $translateLabel('NEW_WINDOW') }}</option>
          <option value="embedded">{{ $translateLabel('EMBEDDED') }}</option>
        </select>
      </label>
      <label>
        <input
          v-model="portalEnsureLoginData"
          type="checkbox"
        >
        <translate i18n-key="ENSURE_LOGIN" />
      </label>
      <label>
        <input
          v-model="portalShowUmcData"
          type="checkbox"
        >
        <translate i18n-key="SHOW_UMC" />
      </label>
      <button class="primary edit-mode-side-navigation__save-button">
        <portal-icon
          icon="save"
        />
        <translate
          i18n-key="SAVE"
        />
      </button>
    </form>
  </nav>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import { udmPut } from '@/jsHelper/umc';
import Translate from '@/i18n/Translate.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import ImageUpload from '@/components/widgets/ImageUpload.vue';
import LocaleInput from '@/components/widgets/LocaleInput.vue';

interface EditModeSideNavigationData {
  portalLogoData: string,
  portalNameData: Record<string, string>,
  portalBackgroundData: string,
  portalDefaultLinkTargetData: string,
  portalShowUmcData: boolean,
  portalEnsureLoginData: boolean,
}

export default defineComponent({
  name: 'EditModeSideNavigation',
  components: {
    Translate,
    PortalIcon,
    ImageUpload,
    LocaleInput,
  },
  data(): EditModeSideNavigationData {
    return {
      portalLogoData: '',
      portalNameData: {},
      portalBackgroundData: '',
      portalDefaultLinkTargetData: 'embedded',
      portalShowUmcData: false,
      portalEnsureLoginData: false,
    };
  },
  computed: {
    ...mapGetters({
      portalDn: 'portalData/getPortalDn',
      portalName: 'portalData/portalName',
      portalLogo: 'portalData/portalLogo',
      portalBackground: 'portalData/portalBackground',
      portalShowUmc: 'portalData/portalShowUmc',
      portalEnsureLogin: 'portalData/portalEnsureLogin',
      portalDefaultLinkTarget: 'portalData/portalDefaultLinkTarget',
    }),
  },
  updated() {
    this.update();
  },
  created() {
    // get initial logo data
    this.portalLogoData = this.portalLogo || '';
    this.portalNameData = this.portalName;
    this.portalBackgroundData = this.portalBackground || '';
    this.portalShowUmcData = this.portalShowUmc;
    this.portalEnsureLoginData = this.portalEnsureLogin;
    this.portalDefaultLinkTargetData = this.portalDefaultLinkTarget;
  },
  methods: {
    update() {
      this.$store.dispatch('portalData/setPortalName', this.portalNameData);
      this.$store.dispatch('portalData/setPortalLogo', this.portalLogoData);
      this.$store.dispatch('portalData/setPortalBackground', this.portalBackgroundData);
    },
    validate() {
      const errors: Record<string, string> = {};
      if (!this.portalNameData.en_US) {
        errors.name = 'ERROR_ENTER_TITLE';
      }
      return errors;
    },
    async saveChanges() {
      const errors = this.validate();
      if (Object.keys(errors).length > 0) {
        this.$el.querySelectorAll('input').forEach((input) => {
          if (input.name) {
            if (input.name in errors) {
              input.setAttribute('invalid', 'invalid');
            } else {
              input.removeAttribute('invalid');
            }
          }
        });
        const description = Object.values(errors)
          .map((err) => this.$translateLabel(err))
          .join('</li><li>');
        this.$store.dispatch('notifications/addErrorNotification', {
          title: this.$translateLabel('ERROR_ON_VALIDATION'),
          description: `<ul><li>${description}</li></ul>`,
        });
        return;
      }
      let logo: string | null = null;
      if (this.portalLogoData.startsWith('data:')) {
        logo = this.portalLogoData.split(',')[1];
      } else if (this.portalLogoData === '') {
        logo = '';
      }
      let background: string | null = null;
      if (this.portalBackgroundData.startsWith('data:')) {
        background = this.portalBackgroundData.split(',')[1];
      } else if (this.portalBackgroundData === '') {
        background = '';
      }
      const displayName = Object.entries(this.portalNameData);
      const showUmc = this.portalShowUmcData;
      const ensureLogin = this.portalEnsureLoginData;
      const defaultLinkTarget = this.portalDefaultLinkTargetData;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const attrs: any = { displayName, showUmc, ensureLogin, defaultLinkTarget };
      if (logo !== null) {
        attrs.logo = logo;
      }
      if (background !== null) {
        attrs.background = background;
      }
      try {
        this.$store.dispatch('activateLoadingState');
        await udmPut(this.portalDn, attrs);
        await this.$store.dispatch('portalData/waitForChange', {
          retries: 10,
          adminMode: false,
        });
        this.$store.dispatch('portalData/setEditMode', false);
        this.$store.dispatch('navigation/setActiveButton', '');
      } catch (error) {
        this.$store.dispatch('notifications/addErrorNotification', {
          title: 'Update failed',
          description: `'Saving the portal failed: ${error}'`,
        });
      }
      this.$store.dispatch('deactivateLoadingState');
    },
  },
});
</script>

<style lang="stylus">
.edit-mode-side-navigation
  &__form
    height: auto
    overflow: auto
    padding: calc(2 * var(--layout-spacing-unit))

    input
      width: 18rem
      &[type=checkbox]
        margin-left: 0
  &__save-button
    margin-top: calc(2 * var(--layout-spacing-unit))
</style>
