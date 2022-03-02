/*
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
*/

import 'cypress-file-upload';
import 'cypress-axe';
// import terminalLog from './terminallog';

beforeEach(() => {
  cy.setCookie('UMCLang', 'de_DE');
  cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_in.json' });
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.visit('/');
  cy.get('main.cookie-banner + footer button.primary').click();

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

    cy.fixture(fileName).then(fileContent => {
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
    cy.get('[data-test="notification--error"]').should('exist');

    cy.get('[data-test="closeNotification--error"]').click();

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
      }
    },
    cy.terminalLog, {
      skipFailures: true
    });
  });
});

const openEditmode = () => {
    // Open Editmode
    cy.get('[data-test="navigationbutton"]').click();
    cy.get('[data-test="openEditmodeButton"]').click();
    cy.get('[data-test="settingsbutton"]').click();
    cy.get('.edit-mode-side-navigation__form').should('be.visible');
}
