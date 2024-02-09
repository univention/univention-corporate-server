/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

export const mockReturnValue = function<ValueType> (fn, value: ValueType): void {
  const fnMock = fn as jest.Mocked<typeof fn>;
  fnMock.mockReturnValue(value);
};

export default {};
