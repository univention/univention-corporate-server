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
  <nav
    class="portal-sidenavigation"
    @keydown.esc="closeNavigation"
  >
    <h2
      class="edit-mode-side-navigation__headline"
    >
      {{ PORTAL_SETTINGS }}
    </h2>
    <form
      class="edit-mode-side-navigation__form"
      @submit.prevent="saveChanges"
    >
      <image-upload
        v-model="portalLogoData"
        :label="PORTAL_LOGO"
        :tabindex="tabindex"
      />
      <locale-input
        v-model="portalNameData"
        :i18n-label="NAME"
        :tabindex="tabindex"
        name="name"
        @update:modelValue="update"
      />
      <image-upload
        v-model="portalBackgroundData"
        :label="BACKGROUND"
        :tabindex="tabindex"
      />
      <label>
        {{ DEFAULT_LINK_BEHAVIOUR }}
        <select
          v-model="portalDefaultLinkTargetData"
          :tabindex="tabindex"
        >
          <option value="samewindow">{{ SAME_TAB }}</option>
          <option value="newwindow">{{ NEW_TAB }}</option>
          <option value="embedded">{{ EMBEDDED }}</option>
        </select>
      </label>
      <label class="edit-mode-side-navigation__checkbox">
        <input
          v-model="portalEnsureLoginData"
          type="checkbox"
          :tabindex="tabindex"
        >
        {{ USERS_REQUIRED_TO_LOGIN }}
      </label>
      <label class="edit-mode-side-navigation__checkbox">
        <input
          v-model="portalShowUmcData"
          type="checkbox"
          :tabindex="tabindex"
        >
        {{ SHOW_LOCAL_UMC_MODULES }}

      </label>
      <button
        class="primary edit-mode-side-navigation__save-button"
        data-test="editModeSideNavigation--Save"
        :tabindex="tabindex"
      >
        <portal-icon
          icon="save"
        />
        <span>
          {{ SAVE }}
        </span>
      </button>
    </form>
  </nav>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import { udmPut } from '@/jsHelper/umc';
import activity from '@/jsHelper/activity';
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
      activityLevel: 'activity/level',
    }),
    PORTAL_LOGO(): string {
      return _('Portal logo');
    },
    BACKGROUND(): string {
      return _('Background');
    },
    DEFAULT_LINK_BEHAVIOUR(): string {
      return _('Default link behaviour for portal entries');
    },
    SAME_TAB(): string {
      return _('Same tab');
    },
    NEW_TAB(): string {
      return _('New tab');
    },
    EMBEDDED(): string {
      return _('Embedded');
    },
    USERS_REQUIRED_TO_LOGIN(): string {
      return _('Users are required to login');
    },
    SHOW_LOCAL_UMC_MODULES(): string {
      return _('Show local UMC modules');
    },
    SAVE(): string {
      return _('Save');
    },
    NAME(): string {
      return _('Name');
    },
    PORTAL_SETTINGS(): string {
      return _('Portal settings');
    },
    tabindex(): number {
      return activity(['header-settings'], this.activityLevel);
    },
  },
  updated() {
    this.update();
    if (this.activityLevel === 'modal') {
      this.$store.dispatch('activity/setLevel', 'header-settings');
    }
  },
  created() {
    this.$store.dispatch('modal/disableBodyScrolling');
    // get initial logo data
    this.portalLogoData = this.portalLogo || '';
    this.portalNameData = this.portalName;
    this.portalBackgroundData = this.portalBackground || '';
    this.portalShowUmcData = this.portalShowUmc;
    this.portalEnsureLoginData = this.portalEnsureLogin;
    this.portalDefaultLinkTargetData = this.portalDefaultLinkTarget;
  },
  methods: {
    closeNavigation(): void {
      this.$store.dispatch('navigation/setActiveButton', '');
      this.$store.dispatch('activity/setRegion', 'portal-header');
    },
    update() {
      this.$store.dispatch('portalData/setPortalName', this.portalNameData);
      this.$store.dispatch('portalData/setPortalLogo', this.portalLogoData);
      this.$store.dispatch('portalData/setPortalBackground', this.portalBackgroundData);
    },
    validate() {
      const errors: Record<string, string> = {};
      if (!this.portalNameData.en_US) {
        errors.name = _('Please enter a display name');
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
          .map((err) => _('%(key1)s', { key1: err }))
          .join('</li><li>');
        this.$store.dispatch('notifications/addErrorNotification', {
          title: _('Error on validation'),
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
  &__headline
    padding: 0 calc(2 * var(--layout-spacing-unit))
    margin-bottom: 0
  &__form
    height: auto
    overflow: auto
    padding: calc(2 * var(--layout-spacing-unit))

    input
      width: 18rem
      &[type=checkbox]
        margin-left: 0

    .image-upload:first-child label
      margin-top: 0
  &__save-button
    margin-top: calc(2 * var(--layout-spacing-unit))
  &__checkbox
    display: flex
</style>
