<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'FormCheckMixin',
  data() {
    return {
      error: {},
    };
  },
  computed: {
    ...mapGetters({
      getModalError: 'modal/getModalError',
    }),
  },
  created() {
    // set error object
    const errorObject = {};
    const props = Object.getOwnPropertyNames(this.modelValueData);
    let i = 0;
    for (i; i < props.length; i += 1) {
      errorObject[props[i]] = false;
    }
  },
  methods: {
    checkFormInput() {
      const props = Object.getOwnPropertyNames(this.modelValueData);
      const reqFields = this.requiredFields;

      const modalError = this.getModalError;
      let i = 0;
      for (i; i < props.length; i += 1) {
        // check if we need to test for errors
        if (reqFields.includes(props[i])) {
          if (this.modelValueData[props[i]] === '') {
            this.error[props[i]] = true;

            if (!modalError.includes(`${this.label}_${[props[i]]}`)) {
              this.$store.dispatch('modal/setModalError', `${this.label}_${[props[i]]}`);
            }
          } else {
            this.error[props[i]] = false;
            this.$store.dispatch('modal/removeModalErrorItem', `${this.label}_${[props[i]]}`);
          }
        }
      }
    },
  },
});
</script>

<style>
</style>
