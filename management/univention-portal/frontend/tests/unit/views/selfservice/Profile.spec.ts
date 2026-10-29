/**
  SPDX-FileCopyrightText: 2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
* */

import { umcCommand } from '@/jsHelper/umc';
import Profile from '@/views/selfservice/Profile.vue';

jest.mock('@/jsHelper/umc', () => ({
  umcCommand: jest.fn(),
  umcCommandWithStandby: jest.fn(),
}));

const mockedUmcCommand = umcCommand as jest.Mock;

function createContext() {
  return {
    credentials: { username: 'user', password: 'secret' },
    $store: { dispatch: jest.fn() },
    $router: { push: jest.fn() },
    $refs: { saveButton: { focus: jest.fn() } },
    errorDialog: { showError: jest.fn(() => Promise.resolve()) },
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const save = (Profile as any).methods.save as (values: Record<string, unknown>) => Promise<void>;

describe('Profile save', () => {
  afterEach(() => {
    mockedUmcCommand.mockReset();
  });

  test('shows a success notification and opens the portal', async () => {
    mockedUmcCommand.mockResolvedValue(true);
    const context = createContext();

    await save.call(context, { jpegPhoto: 'data' });

    expect(mockedUmcCommand).toHaveBeenCalledWith('passwordreset/set_user_attributes', {
      attributes: { jpegPhoto: 'data' },
      username: 'user',
      password: 'secret',
    });
    expect(context.$store.dispatch).toHaveBeenCalledWith('notifications/addSuccessNotification', expect.anything());
    expect(context.$router.push).toHaveBeenCalledWith({ name: 'portal' });
    expect(context.errorDialog.showError).not.toHaveBeenCalled();
  });

  test('shows the error message of the server', async () => {
    mockedUmcCommand.mockRejectedValue({ message: 'Upload rejected: malware was detected in the file.' });
    const context = createContext();

    await save.call(context, { jpegPhoto: 'data' });

    expect(context.errorDialog.showError).toHaveBeenCalledWith('Upload rejected: malware was detected in the file.');
    expect(context.$router.push).not.toHaveBeenCalled();
    expect(context.$store.dispatch).not.toHaveBeenCalledWith('notifications/addSuccessNotification', expect.anything());
  });
});
