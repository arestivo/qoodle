## Why

Managing large numbers of question templates is cumbersome. After importing many templates via the YAML import command, users need to organize them into appropriate subjects. Currently, templates must be moved one at a time through the edit form, which is time-consuming.

Similarly, deleting multiple obsolete templates requires navigating to each template individually.

## What Changes

Add bulk selection and actions to the question template list page:

1. **Checkbox selection**: Add checkboxes to each template row, following the pattern used in `pool_template_add.html`
2. **Select All/None buttons**: Quick selection controls in the table header
3. **Bulk action bar**: A sticky/fixed action bar at the bottom of the page (appears when templates are selected)
4. **Move to Subject action**: Move selected templates to a chosen subject
5. **Delete action**: Delete all selected templates (with confirmation)

## Capabilities

### New Capabilities

- **Bulk template selection**: Select multiple templates using checkboxes
- **Bulk move to subject**: Move multiple templates to a different subject in one action
- **Bulk delete**: Delete multiple templates at once with confirmation

### Modified Capabilities

- **Question list view**: Add checkbox column and bulk action controls

## Impact

- The question list template (`question_list.html`) will be modified to include checkboxes and bulk action controls
- New view(s) will be added to handle bulk operations (move and delete)
- JavaScript will handle the bulk action bar visibility and form submission
- No changes to the QuestionTemplate model are required
