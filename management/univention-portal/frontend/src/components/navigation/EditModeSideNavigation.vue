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
  <nav
    class="portal-sidenavigation"
    @keydown.esc="closeNavigation"
  >
    <h2
      class="edit-mode-side-navigation__headline"
    >
      {{ PORTAL_SETTINGS }}
    </h2>
    <my-form
      ref="form"
      v-model="formValues"
      :widgets="formWidgetsWithTabindex"
      class="edit-mode-side-navigation__form"
    >
      <button
        class="primary edit-mode-side-navigation__save-button"
        data-test="editModeSideNavigation--Save"
        type="submit"
        :tabindex="tabindex"
        @click.prevent="onSave"
      >
        <portal-icon
          icon="save"
        />
        <span>
          {{ SAVE }}
        </span>
      </button>
    </my-form>
  </nav>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import { udmPut } from '@/jsHelper/umc';
import activity from '@/jsHelper/activity';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import MyForm from '@/components/forms/Form.vue';
import { validateAll, allValid } from '@/jsHelper/forms';

interface EditModeSideNavigationData {
  formWidgets: any[],
  formValues: any,
}

export default defineComponent({
  name: 'EditModeSideNavigation',
  components: {
    PortalIcon,
    MyForm,
  },
  data(): EditModeSideNavigationData {
    return {
      formWidgets: [{
        type: 'ImageUploader',
        name: 'logo',
        label: _('Portal logo'),
        extraLabel: _('Portal logo'),
      }, {
        type: 'LocaleInput',
        name: 'displayName',
        label: _('Name'),
        i18nLabel: _('Name'),
        required: true,
      }, {
        type: 'ImageUploader',
        name: 'background',
        label: _('Background'),
        extraLabel: _('Background'),
      }, {
        type: 'ComboBox',
        name: 'defaultLinkTarget',
        label: _('Default link behaviour for portal entries'),
        options: [{
          id: 'samewindow',
          label: _('Same tab'),
        }, {
          id: 'newwindow',
          label: _('New tab'),
        }, {
          id: 'embedded',
          label: _('Embedded'),
        }],
      }, {
        type: 'CheckBox',
        name: 'ensureLogin',
        label: _('Users are required to login'),
      }, {
        type: 'CheckBox',
        name: 'showUmc',
        label: _('Show local UMC modules'),
      }],
      formValues: {
        logo: '',
        displayName: {
          en_US: '',
        },
        background: '',
        defaultLinkTarget: 'embedded',
        ensureLogin: false,
        showUmc: false,
      },
    };
  },
  watch: {
    'formValues.logo': function () {
      this.$store.dispatch('portalData/setPortalLogo', this.formValues.logo);
    },
    'formValues.displayName': {
      handler() {
        this.$store.dispatch('portalData/setPortalName', this.formValues.displayName);
      },
      deep: true,
    },
    'formValues.background': function () {
      this.$store.dispatch('portalData/setPortalBackground', this.formValues.background);
    },
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
    PORTAL_SETTINGS(): string {
      return _('Portal settings');
    },
    SAVE(): string {
      return _('Save');
    },
    tabindex(): number {
      return activity(['header-settings'], this.activityLevel);
    },
    formWidgetsWithTabindex(): any {
      return this.formWidgets.map((widget) => {
        widget.tabindex = this.tabindex;
        return widget;
      });
    },
  },
  updated() {
    if (this.activityLevel === 'modal') {
      this.$store.dispatch('activity/setLevel', 'header-settings');
    }
  },
  created() {
    this.$store.dispatch('modal/disableBodyScrolling');
    this.formValues.logo = this.portalLogo || '';
    this.formValues.displayName = this.portalName;
    this.formValues.background = this.portalBackground || '';
    this.formValues.defaultLinkTarget = this.portalDefaultLinkTarget;
    this.formValues.ensureLogin = this.portalEnsureLogin;
    this.formValues.showUmc = this.portalShowUmc;
  },
  methods: {
    closeNavigation(): void {
      this.$store.dispatch('navigation/setActiveButton', '');
      this.$store.dispatch('activity/setRegion', 'portal-header');
    },
    onSave() {
      validateAll(this.formWidgets, this.formValues);
      if (!allValid(this.formWidgets)) {
        // @ts-ignore TODO
        this.$refs.form.focusFirstInvalid();
        return;
      }
      this.saveChanges();
    },
    async saveChanges() {
      let logo: string | null = null;
      if (this.formValues.logo.startsWith('data:')) {
        logo = this.formValues.logo.split(',')[1];
      } else if (this.formValues.logo === '') {
        logo = '';
      }
      let background: string | null = null;
      if (this.formValues.background.startsWith('data:')) {
        background = this.formValues.background.split(',')[1];
      } else if (this.formValues.background === '') {
        background = '';
      }
      const displayName = Object.entries(this.formValues.displayName);
      const showUmc = this.formValues.showUmc;
      const ensureLogin = this.formValues.ensureLogin;
      const defaultLinkTarget = this.formValues.defaultLinkTarget;
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
</style>
