/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';
import MultiInput from '@/components/widgets/MultiInput.vue';
import IconButton from '@/components/globals/IconButton.vue';
import FormElement from '@/components/forms/FormElement.vue';
import Vuex from 'vuex';
import activity from '@/store/modules/activity';

const multiInputProps = {
  modelValue: [''],
  subtypes: [{ type: 'TextBox', name: '', label: '', required: false, readonly: false }],
  invalidMessage: { all: '', values: [] },
  invalidMessageId: '',
  extraLabel: 'Label',
};

const store = new Vuex.Store({
  modules: {
    activity: {
      getters: activity.getters,
      namespaced: true,
    },
  },
});

store.dispatch = jest.fn();

let wrapper;

beforeEach(async () => {
  wrapper = await mount(MultiInput, {
    propsData: multiInputProps,
    children: [IconButton, FormElement],
    global: {
      plugins: [store],
    },
  });
});

afterEach(() => {
  wrapper.unmount();
});

describe('MultiInput.vue', () => {
  test('if Button with label "Add entry" exists', async () => {
    const addEntryButton = await wrapper.find('[data-test="multi-input-add-entry-button"]');
    expect(addEntryButton.attributes('aria-label')).toBe(`Add new ${multiInputProps.extraLabel}`);
  });

  test('if remove-entry button exists', async () => {
    const removeEntryButton = await wrapper.find('[data-test="multi-input-remove-entry-button-0"]');
    expect(removeEntryButton.attributes('aria-label')).toBe(`Remove ${multiInputProps.extraLabel} 1`);
  });

  test('if the .multi-input__row is working for singleline', async () => {
    // Since multiInputProps.subtypes has only one element in the array, we don't need to set props,:
    // and can directly check what we expect
    const multiInputRow = wrapper.find('[data-test="multi-input-row"]');
    expect(multiInputRow.classes()).toContain('multi-input__row--singleline');
    expect(multiInputRow.classes()).not.toContain('multi-input__row--multiline');
  });

  test('if the .multi-input__row is working for multiline', async () => {
  //  Setting the needed props to test the component
    const multiSubType = [{ type: 'TextBox', name: '', label: 'Street', required: false, readonly: false }, { type: 'TextBox', name: '', label: 'Postal code', required: false, readonly: false }];
    wrapper.setProps({ subtypes: multiSubType, invalidMessageId: '' });
    await wrapper.vm.$nextTick();

    const multiInputRow = wrapper.find('[data-test="multi-input-row"]');
    expect(multiInputRow.classes()).toContain('multi-input__row--multiline');
    expect(multiInputRow.classes()).not.toContain('multi-input__row--singleline');
  });

  test('if the .multi-input__row has class multi-input__row--invalid if rowInvalidMessage(valIdx) !== ""', async () => {
    // Set wrapperprops with needed values to recieve the desired results
    const newInvalidMessage = { all: '', values: ['not enough arguments'] };

    wrapper.setProps({ invalidMessage: newInvalidMessage, invalidMessageId: '' });
    await wrapper.vm.$nextTick();

    const multiInputRow = wrapper.find('[data-test="multi-input-row"]');
    // Since this.rowInvalidMessage returns '' when the subtypes.length equals 1,
    // we expect NOT to find the class 'multi-input__row--invalid' in multiInputRow
    // even if newInvalidMessage has a value set.
    expect(multiInputRow.classes()).not.toContain('multi-input__row--invalid');

    const multiSubType = [{ type: 'TextBox', name: '', label: 'Street', required: false, readonly: false }, { type: 'TextBox', name: '', label: 'Postal code', required: false, readonly: false }];
    wrapper.setProps({ subtypes: multiSubType });
    await wrapper.vm.$nextTick();

    // after updating the wrapper with an multiSubType Object we
    expect(multiInputRow.classes()).toContain('multi-input__row--invalid');
  });

  test('if the onUpdate is called after changes in input', async () => {
    const onUpdateSpy = jest.spyOn(wrapper.vm, 'onUpdate');
    const input = wrapper.find('input');
    await input.setValue('test input value');
    await wrapper.vm.$nextTick();

    expect(onUpdateSpy).toHaveBeenCalled();
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');
  //  2. update:modelValue is emitted with desired value
  });

  test('if the addEntry is called after button click', async () => {
    const addEntrySpy = jest.spyOn(wrapper.vm, 'addEntry');
    const addEntryButton = await wrapper.find('[data-test="multi-input-add-entry-button"]');
    addEntryButton.trigger('click');
    await wrapper.vm.$nextTick();

    expect(addEntrySpy).toHaveBeenCalled();
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');
    expect(wrapper.vm.modelValue.length).toBe(2);
    expect(store.dispatch).toHaveBeenCalledWith('activity/setMessage', `${wrapper.vm.extraLabel} ${wrapper.vm.modelValue.length} added`);
  });

  test('if the newRow is called in addEntry Method', async () => {
    const newRowSpy = jest.spyOn(wrapper.vm, 'newRow');
    const addEntryButton = await wrapper.find('[data-test="multi-input-add-entry-button"]');
    addEntryButton.trigger('click');
    await wrapper.vm.$nextTick();

    expect(newRowSpy).toHaveBeenCalled();
  });

  test('if the newRow and removeEntry is called in removeEntry Method', async () => {
    // newRow needs to be called, if user tries to remove last row
    // we will also test removeEntry and update:modelValue
    const newRowSpy = jest.spyOn(wrapper.vm, 'newRow');

    const removeEntrySpy = jest.spyOn(wrapper.vm, 'removeEntry');
    const removeEntryButton = await wrapper.find('[data-test="multi-input-remove-entry-button-0"]');
    removeEntryButton.trigger('click');
    await wrapper.vm.$nextTick();

    expect(newRowSpy).toHaveBeenCalled();
    expect(removeEntrySpy).toHaveBeenCalled();
    expect(store.dispatch).toHaveBeenCalledWith('activity/setMessage', `${wrapper.vm.extraLabel} 1 removed`);
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');
  });

  test('if the getSubtypeWidget is called correctly', async () => {
    // getSubtypeWidget is called in each iteration in the subtypes for loop.
    // It is used to pass the correct widget object in form-element
    wrapper.unmount();
    const getSubtypeWidgetSpy = jest.spyOn(MultiInput.methods, 'getSubtypeWidget');
    wrapper = await mount(MultiInput, {
      propsData: multiInputProps,
      children: [IconButton, FormElement],
      global: {
        plugins: [store],
      },
    });
    await wrapper.vm.$nextTick();

    expect(getSubtypeWidgetSpy).toHaveBeenCalledWith(multiInputProps.subtypes[0], 0, 0);
  });
});
