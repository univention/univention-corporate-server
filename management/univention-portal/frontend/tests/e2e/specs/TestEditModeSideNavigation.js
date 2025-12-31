/*
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
*/

import 'cypress-file-upload';
import 'cypress-axe';
// import terminalLog from './terminallog';

const openEditmode = () => {
  // Open Editmode
  cy.get('[data-test="navigationbutton"]').click();
  cy.get('[data-test="openEditmodeButton"]').click();
  cy.get('[data-test="settingsbutton"]').click();
  cy.get('.edit-mode-side-navigation__form').should('be.visible');
};

beforeEach(() => {
  cy.setCookie('UMCLang', 'de_DE');
  cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_in.json' });
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.visit('/');
  cy.get('main.cookie-banner + footer button.button--primary').click();

  cy.injectAxe();
  openEditmode();
});

describe('Test Editmode Side navigation', () => {
  it('Open Editmode sidenavigation and edit general portal data.', () => {
    // Assert: No Image in .image-upload__canvas
    cy.get('[data-test=imageUploadCanvas--Portal-Logo] img').should('not.exist');
    cy.get('[data-test=imageUploadButton--Portal-Logo]').click();

    // programmatically upload the logo
    const fileName = 'images/logo.svg';

    cy.fixture(fileName).then((fileContent) => {
      cy.get('[data-test=imageUploadFileInput--Portal-Logo]').attachFile(
        { fileContent, fileName, mimeType: 'image/svg+xml' },
      );
    });

    // Assert: Image in .image-upload__canvas should exist
    cy.get('[data-test=imageUploadCanvas--Portal-Logo] img').should('exist');

    // Assert: click on remove: Image in .image-upload__canvas should not exist anymore
    cy.get('[data-test=imageRemoveButton--Portal-Logo]').click();
    cy.get('[data-test=imageUploadCanvas--Portal-Logo] img').should('not.exist');
  });

  it('Test Local Input and required fields', () => {
    cy.get('[data-test="localeInput--Name"]').clear();
    cy.get('[data-test="notification--error"]').should('not.exist');
    cy.get('[data-test="editModeSideNavigation--Save"]').click();

    // assert Error Notification due to empty input
    cy.get('.form-element--LocaleInput.form-element--invalid .input-error-message').contains('This value is required');

    // Enter Text and Save then.
    cy.get('[data-test="localeInput--Name"]').type('Univention Portal');
    cy.get('[data-test="editModeSideNavigation--Save"]').click();

    // TODO: Check if Changes are seen in new portal.json
  });

  it('make a11y test', () => {
    // Inject the axe-core library
    // first a11y test
    cy.checkA11y('.edit-mode-side-navigation__form',
      {
        runOnly: {
          type: 'tag',
          values: ['wcag21aa'],
        },
      },
      cy.terminalLog, {
        skipFailures: true,
      });
  });
});
