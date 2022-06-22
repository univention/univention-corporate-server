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
  <edit-widget
    ref="editWidget"
    v-model:form-values="formValues"
    :form-widgets="formWidgetsComputed"
    :label="label"
    :can-remove="!!modelValue.dn"
    :model="$data"
    @unlink="unlink"
    @remove="remove"
    @save="finish"
    @submit="submit"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import { removeEntryFromSuperObj, addEntryToSuperObj, put, add, remove } from '@/jsHelper/admin';
import activity from '@/jsHelper/activity';
import EditWidget from '@/components/admin/EditWidget.vue';
import { validateAll, allValid, validateInternalName } from '@/jsHelper/forms';

interface AdminEntryData {
  formWidgets: any,
  formValues: any,
}

export default defineComponent({
  name: 'FormEntryEdit',
  components: {
    EditWidget,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    superDn: {
      type: String,
      required: true,
    },
    fromFolder: {
      type: Boolean,
      required: true,
    },
    modelValue: {
      type: Object,
      required: true,
    },
  },
  data(): AdminEntryData {
    return {
      formWidgets: [{
        type: 'TextBox',
        name: 'name',
        label: _('Internal name'),
        required: true,
        autocomplete: 'off',
        validators: [validateInternalName],
      }, {
        type: 'LocaleInput',
        name: 'title',
        required: true,
        label: _('Name'),
        i18nLabel: _('Name'),
      }, {
        type: 'LocaleInput',
        name: 'description',
        required: true,
        label: _('Description'),
        i18nLabel: _('Description'),
      }, {
        type: 'LocaleInput',
        name: 'keywords',
        label: _('Keywords'),
        i18nLabel: _('Keywords'),
      }, {
        type: 'CheckBox',
        name: 'activated',
        label: _('Activated'),
      }, {
        // type: type is set in the 'formWidgetsComputed' computed property
        name: 'links',
        label: _('Links'),
      }, {
        type: 'ComboBox',
        name: 'linkTarget',
        label: _('Way of opening links'),
        options: [{
          id: 'useportaldefault',
          label: _('Use default of portal'),
        }, {
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
        type: 'ImageUploader',
        name: 'logo',
        label: _('Icon'),
        extraLabel: _('Icon'),
      }, {
        type: 'TextBox',
        name: 'backgroundColor',
        label: _('Background color'),
      }, {
        type: 'MultiSelect',
        name: 'allowedGroups',
        label: _('Can only be seen by these groups'),
      }, {
        type: 'CheckBox',
        name: 'anonymous',
        label: _('Only visible if not logged in'),
      }],
      formValues: {
        name: '',
        title: {
          en_US: '',
        },
        description: {
          en_US: '',
        },
        keywords: {
          en_US: '',
        },
        activated: true,
        linkTarget: 'useportaldefault',
        logo: '',
        backgroundColor: '',
        allowedGroups: [],
        anonymous: false,
        links: {
          en_US: '',
        },
      },
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
      portalFolders: 'portalData/portalFolders',
      activityLevel: 'activity/level',
      availableLocales: 'locale/getAvailableLocales',
    }),
    formWidgetsComputed(): any {
      return this.formWidgets.map((widget) => {
        if (widget.name === 'name') {
          widget.readonly = !!this.modelValue.dn;
        }
        if (widget.name === 'links') {
          widget.type = Array.isArray(this.formValues.links) ? 'LinkWidget' : 'LocaleInput';
          if (widget.type === 'LocaleInput') {
            widget.i18nLabel = _('Links');
            widget.required = true;
          } else {
            widget.validators = [(_widget, value) => {
              const hasEnglishEntry = value.some((link) => link.locale === 'en_US' && !!link.value);
              if (!hasEnglishEntry) {
                return _('Please enter at least one English link');
              }
              return '';
            }];
          }
        }
        widget.tabindex = activity(['modal'], this.activityLevel);
        return widget;
      });
    },
    superObjs(): any[] { // eslint-disable-line @typescript-eslint/no-explicit-any
      if (this.fromFolder) {
        return this.portalFolders;
      }
      return this.portalCategories;
    },
  },
  created(): void {
    const dn = this.modelValue.dn;
    if (dn) {
      this.formValues.name = dn.slice(3, dn.indexOf(','));
    }
    const links = this.modelValue.links;
    if (Array.isArray(links) && links.length > 0) {
      let canUseLocaleInput = true;
      const uniqueLocales: string[] = [];
      links.forEach((lnk) => {
        if (uniqueLocales.includes(lnk.locale)) {
          canUseLocaleInput = false;
        } else {
          uniqueLocales.push(lnk.locale);
        }
      });
      if (!uniqueLocales.includes('en_US')) {
        canUseLocaleInput = false;
      }
      if (canUseLocaleInput) {
        const simpleLinks = links.reduce((dict, lnk) => {
          dict[lnk.locale] = lnk.value;
          return dict;
        }, {});
        this.formValues.links = simpleLinks;
      } else {
        this.formValues.links = links;
      }
    }
    this.formValues.title = { ...(this.modelValue.title ?? this.formValues.title) };
    this.formValues.description = { ...(this.modelValue.description ?? this.formValues.description) };
    this.formValues.keywords = { ...(this.modelValue.keywords ?? this.formValues.keywords) };
    this.formValues.activated = this.modelValue.activated ?? this.formValues.activated;
    this.formValues.linkTarget = this.modelValue.originalLinkTarget ?? this.formValues.linkTarget;
    this.formValues.logo = this.modelValue.pathToLogo ?? this.formValues.logo;
    this.formValues.backgroundColor = this.modelValue.backgroundColor ?? this.formValues.backgroundColor;
    this.formValues.allowedGroups = [...(this.modelValue.allowedGroups ?? this.formValues.allowedGroups)];
    this.formValues.anonymous = this.modelValue.anonymous ?? this.formValues.anonymous;
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('activity/setRegion', 'portalCategories');
    },
    async unlink() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      // console.info('Removing', dn, 'from', this.superDn);
      const success = await removeEntryFromSuperObj(this.superDn, this.superObjs, dn, this.$store, _('Entry successfully unlinked'), _('Entry could not be unlinked'));
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    async remove() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      // console.info('Deleting', dn, 'completely');
      const success = await remove(dn, this.$store, _('Entry successfully removed'), _('Entry could not be removed'));
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    async finish() {
      this.$store.dispatch('activateLoadingState');
      let success = false;
      let links = this.formValues.links;
      if (Array.isArray(links)) {
        links = links.filter((lnk) => !!lnk.value).map((lnk) => [lnk.locale, lnk.value]);
      } else {
        links = Object.keys(links).reduce((acc: any, locale) => {
          acc.push([locale, links[locale]]);
          return acc;
        }, []);
      }
      const attrs = {
        name: this.formValues.name,
        displayName: Object.entries(this.formValues.title),
        description: Object.entries(this.formValues.description),
        keywords: Object.entries(this.formValues.keywords),
        activated: this.formValues.activated,
        link: links,
        linkTarget: this.formValues.linkTarget,
        icon: this.formValues.logo,
        backgroundColor: this.formValues.backgroundColor,
        allowedGroups: this.formValues.allowedGroups,
        anonymous: this.formValues.anonymous,
      };
      if (attrs.icon.startsWith('data:')) {
        attrs.icon = attrs.icon.split(',')[1];
      } else if (attrs.icon === '') {
        attrs.icon = '';
      } else {
        delete attrs.icon;
      }

      if (this.modelValue.dn) {
        // console.info('Modifying', this.modelValue.dn);
        success = await put(this.modelValue.dn, attrs, this.$store, _('Entry could not be modified'), _('Entry successfully modified'));
      } else {
        // console.info('Adding entry');
        const dn = await add('portals/entry', attrs, this.$store, _('Entry could not be added'));
        if (dn) {
          // console.info(dn, 'added');
          success = await addEntryToSuperObj(this.superDn, this.superObjs, dn, this.$store, _('Entry successfully added'), _('Entry could not be added'));
        }
      }
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    submit() {
      validateAll(this.formWidgets, this.formValues);
      if (!allValid(this.formWidgets)) {
        // @ts-ignore
        this.$refs.editWidget.$refs.form.focusFirstInvalid();
        return;
      }
      this.finish();
    },
  },
});
</script>
