/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import LocaleInput from '@/components/widgets/LocaleInput.vue';
import Vuex from 'vuex';
import locale from '@/store/modules/locale';
import modal from '@/store/modules/modal';
import activity from '@/store/modules/activity';

const localeInputProps = {
  modelValue: {
    en_US: '',
  },
  forAttrOfLabel: '',
  invalidMessageId: '',
  name: 'Name of LocaleInput',
  i18nLabel: 'Label of LocaleInput',

};

const localeState = {
  locale: 'de_DE',
};

const modalActions = {
  setShowModalPromise: jest.fn(),
  hideAndClearModal: jest.fn(),
};

const activityActions = {
  setRegion: jest.fn(),
};

const store = new Vuex.Store({
  modules: {
    locale: {
      localeState,
      getters: locale.getters,
      namespaced: true,
    },
    modal: {
      modalActions,
      getters: modal.getters,
      namespaced: true,
    },
    activity: {
      activityActions,
      getters: activity.getters,
      namespaced: true,
    },
  },
});

const mountComponent = () => (mount(LocaleInput, {
  global: {
    plugins: [store],
  },
  propsData: localeInputProps,
}));

describe('LocaleInput Component', () => {
  test('it sets the es_US translation in modelValue correctly', async () => {
    // mount component with empty modelValue
    const wrapper = mountComponent();
    const localeInput = await wrapper.find('[data-test="locale-input"]');
    const input = await localeInput.find('input');
    input.setValue('english word');

    const expected = { en_US: 'english word' };
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.modelValue.en_US).toBe(expected.en_US);
  });

  test('the modalLevel is correct', async () => {
    // if isInModal is true the modalLevel should be 2
    // if not the modalLevel should be 1
    // mount component without inInModal Props
    const wrapper = mountComponent();

    expect(wrapper.vm.translationEditingDialogLevel).toBe(2);

    // change is in ModalProp
    wrapper.setProps({ isInModal: false });
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.translationEditingDialogLevel).toBe(1);
  });

  it.todo('if the correct object will be given to translationEditingDialog');
  //   // the translationEditingDialog accepts only a certain type of object, therefore we need
  //   // to ensure, that the modelValueData is set correctly

  it.todo('if adjustDataStructureForLinks is working as expected');
  //   // Pass a link object type as modelValue
  //   // expect new object to be passed, needed for LocaleInput

  it.todo('if openTranslationEditingDialog will be called');
  //   // ...

  it.todo('if setShowModalPromise will be called');
  //   // Check if Props are prepared
  //   // Check if dispatch is working
  //   // Check if Promise is working

  it.todo('if hideAndClearModal will be called');
  //   // There a two hide and clear promises:
  //   // 1) A "succesful" hide and clear -> with new data
  //   // 2) A Promise called by cancel

  it.todo('if I18N_LABEL is returning the correct labelValue');
  //   // It seems to be an easy thing, but I guess it is not bad, to just start
  //   // to test also the "simple things" for better documentation
  //   // Pass I18n-label as Prop
  //   // Expect computed Property to be desired Output.

  it.todo('if TRANSLATE_TEXT_INPUT is returning the correct labelValue');
  //   // same as above
  //   // It seems to be an easy thing, but I guess it is not bad, to just start
  //   // to test also the "simple things" for better documentation
  //   // Pass I18n-label as Prop
  //   // Expect computed Property to be desired Output.
});
