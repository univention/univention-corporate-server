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
        label="Portal logo"
      />
      <div
        v-for="displayName in displayNames"
        :key="displayName.locale"
      >
        <label>
          Name ({{ displayName.locale }})
        </label>
        <input
          v-model="displayName.name"
        >
      </div>
      <button class="primary">
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

interface LocalizedName {
  locale: string,
  name: string,
}

interface EditModeSideNavigationData {
  portalLogoData: string,
  displayNames: LocalizedName[],
}

export default defineComponent({
  name: 'EditModeSideNavigation',
  components: {
    Translate,
    PortalIcon,
    ImageUpload,
  },
  data(): EditModeSideNavigationData {
    return {
      portalLogoData: '',
      displayNames: [],
    };
  },
  computed: {
    ...mapGetters({
      portalDn: 'portalData/getPortalDn',
      portalName: 'portalData/portalName',
      portalLogo: 'portalData/portalLogo',
    }),
  },
  updated() {
    const name = {};
    this.displayNames.forEach((displayName) => {
      name[displayName.locale] = displayName.name;
    });
    this.$store.dispatch('portalData/setPortalName', name);
    this.$store.dispatch('portalData/setPortalLogo', this.portalLogoData);
  },
  mounted() {
    // get initial logo data
    this.portalLogoData = this.portalLogo || '';

    // set up displayNames from locale data
    this.displayNames = Object.keys(this.portalName).map((locale) => ({
      locale,
      name: this.portalName[locale],
    }));
  },
  methods: {
    async saveChanges() {
      let logo: string | null = null;
      if (this.portalLogoData.startsWith('data:')) {
        logo = this.portalLogoData.split(',')[1];
      } else if (this.portalLogoData === '') {
        logo = '';
      }
      const displayName = this.displayNames.map((displName) => [displName.locale, displName.name]);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const attrs: any = { displayName };
      if (logo !== null) {
        attrs.logo = logo;
      }
      try {
        this.$store.dispatch('activateLoadingState');
        await udmPut(this.portalDn, attrs);
        await this.$store.dispatch('portalData/waitForChange', 10);
        this.$store.dispatch('portalData/setEditMode', false);
        this.$store.dispatch('navigation/setActiveButton', '');
      } catch (error) {
        this.$store.dispatch('notificationBubble/addErrorNotification', {
          bubbleTitle: 'Update failed',
          bubbleDescription: `'Saving the portal failed: ${error}'`,
        });
      }
      this.$store.dispatch('deactivateLoadingState');
    },
  },
});
</script>

<style lang="stylus">
.edit-mode-side-navigation__form
  padding: calc(2 * var(--layout-spacing-unit))
  input
    width: 18rem
</style>
