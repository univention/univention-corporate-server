# Review Guidelines for new Frontend Code

These guidelines serve as an orientation and checklist, when reviewing new widget implementations or other GUI components in the frontend.

> ⚠️ This is a work-in-progress document.
  The guidelines are by no means complete.
  Especially the _Code_ section should be enhanced with further best practice guidelines.
  Remove this comment, once a more tested and proven status of the document is reached.

## Code

* No warnings in eslint
> ☝️ Linting is done automatically before every commit for various files. See [Pre-commit hooks](.pre-commit-config.yaml)
* Code is "clean":
  * Function and file size is kept small and manageable
> ☝️ To avoid confusion: 'Clean Code', as in the book by Robert C. Martin, is not enforced

## Testing

* Currently no requirements for test coverage
* At least one test should exist

## GUI

Important aspects when reviewing the GUI are _accessibility or a11y_, _usability_, _documentation_ and _translations (internationalization or i18n)_

* For every widget, `*.stories.ts` files must exist, to enable manual testing in storybook
* All A11y widgets follow the WCAG guidelines and should be conformant to level AA https://www.w3.org/WAI/WCAG2AA-Conformance
* Storybook automatically checks for violations of a11y rules and suggests usage of ARIA labels
* Important aspects are _keyboard usage_ and _screen reader friendliness_
> ☝️ more info on a11y can be found in the storybook UI (run `yarn storybook` and go to left menu > Accessibility)
* Storybook is also used to document changes and should therefore be reviewed for existing documentation
* If i18n text was added, it should come with German and English translation. See [how to translate](frontend/README.md#translation)

## Organization

### Issue

* The merge request is linked with a GitLab issue
* An issue should contain requirements and acceptance criteria

### Branching

* A merge request and its associated branch only contains a single widget, feature or concern
