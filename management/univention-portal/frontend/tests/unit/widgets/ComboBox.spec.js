/**
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
