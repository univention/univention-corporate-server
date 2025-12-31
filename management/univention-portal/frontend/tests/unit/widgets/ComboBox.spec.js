/**
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { mount } from '@vue/test-utils';

import ComboBox from '@/components/widgets/ComboBox.vue';

const comboBoxOptions = [
  {
    id: 'red',
    label: 'Red',
  },
  {
    id: 'green',
    label: 'Green',
  },
  {
    id: 'blue',
    label: 'Blue',
  },
];

const forAttrOfComboBoxLabel = 'testString';

const comboBoxProps = {
  modelValue: '',
  options: comboBoxOptions,
  forAttrOfLabel: forAttrOfComboBoxLabel,
  name: 'comboBox',
  invalidMessageId: '',
};

let wrapper;

beforeEach(async () => {
  wrapper = await mount(ComboBox, {
    propsData: comboBoxProps,
  });
});

afterEach(() => {
  wrapper.unmount();
});

describe('ComboBox Component', () => {
  test('if user can select option as input', async () => {
    const comboBox = await wrapper.find('[data-test="combo-box"]');

    // select an option and expect the selectvalue to be that option
    const options = comboBox.findAll('option');
    await options[0].setSelected();

    expect(comboBox.element.value).toBe(comboBoxOptions[0].id);
  });

  test('if update:modelValue is emmited on change', async () => {
    // select an option and expect the selectvalue to be that option
    const options = wrapper.findAll('option');
    await options[0].setSelected();

    expect(wrapper.emitted()).toHaveProperty('update:modelValue');
  });

  test('this.invalid should return correct boolean', async () => {
    const comboBox = await wrapper.find('[data-test="combo-box"]');

    // this.invalid returns true if this.invalidMessage has a non-empty string
    expect(wrapper.vm.invalid).toBe(false);
    expect(comboBox.attributes('aria-invalid')).toBe('false');

    await wrapper.setProps({ invalidMessage: 'Invalid Message' });

    expect(comboBox.attributes('aria-invalid')).toBe('true');
    expect(wrapper.vm.invalid).toBe(true);
  });

  test('No other values than those in option array are possible', async () => {
    const comboBox = await wrapper.find('[data-test="combo-box"]');
    const select = wrapper.find('select');
    const textInput = 'wrong-input';
    await select.setValue(textInput);

    expect(comboBox.element.value).not.toBe(textInput);
  });

  test('it has the attribute id with a value from Prop //A11y', async () => {
    const dateBox = await wrapper.find('[data-test="combo-box"]');
    expect(dateBox.attributes('id')).toBe(forAttrOfComboBoxLabel);
  });

  test('if option tag is rendered correctly', async () => {
    const options = wrapper.findAll('option');

    expect(options.length).toBe(comboBoxOptions.length);
    expect(options[0].attributes('value')).toBe('red');
  });
});
