<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <guarded-site
    id="password-forgotten"
    ref="guardedSite"
    :title="TITLE"
    :subtitle="SUBTITLE"
    path="passwordreset/get_reset_methods"
    :password-needed="false"
    :guarded-widgets="formWidgets"
    @loaded="loaded"
    @save="sendToken"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import { umcCommandWithStandby } from '@/jsHelper/umc';
import _ from '@/jsHelper/translate';
import GuardedSite from '@/views/selfservice/GuardedSite.vue';
import { WidgetDefinition } from '@/jsHelper/forms';

interface MethodInfo {
  id: string,
  label: string,
}

interface Data {
  formWidgets: WidgetDefinition[],
}

export default defineComponent({
  name: 'PasswordForgotten',
  components: {
    GuardedSite,
  },
  data(): Data {
    return {
      formWidgets: [],
    };
  },
  computed: {
    TITLE(): string {
      return _('Password forgotten');
    },
    SUBTITLE(): string {
      return _('Forgot your password? Set a new one:');
    },
  },
  methods: {
    loaded(result: MethodInfo[], formValues) {
      this.formWidgets = [{
        type: 'RadioBox',
        name: 'method',
        options: result,
        label: _('Please choose an option to renew your password.'),
        invalidMessage: '',
        required: true,
      }];
      formValues.method = result[0]?.id ?? '';
    },
    sendToken(values) {
      umcCommandWithStandby(this.$store, 'passwordreset/send_token', values)
        .then(() => {
          this.$store.dispatch('notifications/addSuccessNotification', {
            title: _('Token sent'),
            description: _('Successfully sent Token.'),
          });
          this.$router.push({ name: 'selfserviceNewPassword', query: { username: values.username } });
        })
        .catch((error) => {
          (this.$refs.guardedSite as typeof GuardedSite).showError(error.message)
            .then(() => {
              (this.$refs.guardedSite as typeof GuardedSite).refocus();
            });
        });
    },
  },
});
</script>
