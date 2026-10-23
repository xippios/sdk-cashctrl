Source: <https://app.cashctrl.com/static/help/en/api/index.html#/salary/bookentry>\
Fetched: 2026-10-23 (UTC)

## Book entry

The following API endpoints are for managing salary book entries. These are all the journal book entries that are created for a salary statement, either automatically from salary types or manually from payments. Automatically created book entries cannot be manipulated directly, only by changing the salary types.

### Read book entry

Returns a single book entry by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/bookentry/read.json
```

### List book entries

Returns a list of book entries for an order.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/bookentry/list.json
```

### Create book entry

Creates a new book entry. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `creditId` | mandatory, NUMBER | The ID of the account on the credit side. See [Account](https://app.cashctrl.com/static/help/en/api/index.html#/account). |
| `debitId` | mandatory, NUMBER | The ID of the account on the debit side. See [Account](https://app.cashctrl.com/static/help/en/api/index.html#/account). |
| `statementIds` | mandatory, CSV | The IDs of one or multiple salary statements, comma-separated. See [Salary statement](https://app.cashctrl.com/static/help/en/api/index.html#/salary/statement). |
| `amount` | optional, NUMBER | The amount of the book entry (e.g. 125.50). Leave empty to use open amount of salary statement. |
| `date` | optional, DATE | The date of the book entry.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `description` | optional, TEXT, MAX:200 | The description of the book entry. |
| `reference` | optional, TEXT | An optional reference / receipt for the book entry. |
| `statusId` | optional, NUMBER | The ID of the new status for the salary statement(s). See [Salary status](https://app.cashctrl.com/static/help/en/api/index.html#/salary/status). |

#### Endpoint

```
POST /api/v1/salary/bookentry/create.json
```

### Update book entry

Updates an existing book entry. Note that you cannot update book entries that have been automatically created from salary types, only manually created book entries (payments). Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `creditId` | mandatory, NUMBER | The ID of the account on the credit side. See [Account](https://app.cashctrl.com/static/help/en/api/index.html#/account). |
| `debitId` | mandatory, NUMBER | The ID of the account on the debit side. See [Account](https://app.cashctrl.com/static/help/en/api/index.html#/account). |
| `id` | mandatory, NUMBER | The ID of the book entry to update. |
| `amount` | optional, NUMBER | The amount of the book entry (e.g. 125.50). Leave empty to use open amount of salary statement. |
| `date` | optional, DATE | The date of the book entry.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `description` | optional, TEXT, MAX:200 | The description of the book entry. |
| `reference` | optional, TEXT | An optional reference / receipt for the book entry. |
| `statusId` | optional, NUMBER | The ID of the new status for the salary statement(s). See [Salary status](https://app.cashctrl.com/static/help/en/api/index.html#/salary/status). |

#### Endpoint

```
POST /api/v1/salary/bookentry/update.json
```

### Delete book entries

Deletes one or multiple book entries. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/bookentry/delete.json
```

## Category

The following API endpoints are for managing salary categories. These are used to categorize salary types, so that salary types are a bit easier to find (for example in menus). There isn't more to this.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/category/read.json
```

### List categories

Returns a list of categories.

#### Endpoint

```
GET /api/v1/salary/category/list.json
```

### List categories as tree

Returns a hierarchical tree of categories.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:50 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `number` | optional, TEXT, MAX:20 | A number to order by. Must be numeric but can contain a decimal point. Is solely used for ordering, not displayed. |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/salary/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the category to update. |
| `name` | mandatory, TEXT, MAX:50 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `number` | optional, TEXT, MAX:20 | A number to order by. Must be numeric but can contain a decimal point. Is solely used for ordering, not displayed. |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/salary/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/category/delete.json
```

## Certificate

The following API endpoints are for managing salary certificates. Salary certificates are automatically generated from salary statements and thus they can only be read and updated, but not created. Updating a salary certificate can only affect its custom fields and notes, everything else is generated.

### Read certificate

Returns a single salary certificate by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the salary certificate. |

#### Endpoint

```
GET /api/v1/salary/certificate/read.json
```

### List certificates

Returns a list of salary certificates.

#### Parameters

<table>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateEnd'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/certificate/list.json
```

### Export to Excel

Returns an Excel file of the salary certificate list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateEnd'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/certificate/list.xlsx
```

### Export to CSV

Returns a CSV file of the salary certificate list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateEnd'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/certificate/list.csv
```

### Export to PDF

Returns a PDF file of the salary certificate list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateEnd'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/certificate/list.pdf
```

### Update certificate

Updates an existing salary certificate. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the salary certificate to update. |
| `notes` | optional, HTML | Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `valuesLocal` | optional, JSON | Values to print directly on the salary certificate. This overrides any values set on the [employee](https://app.cashctrl.com/static/help/en/api/index.html#/person), which in turn overrides any values set on the [salary certificate template](https://app.cashctrl.com/static/help/en/api/index.html#/salary/certificate/template). This is a map of code -> value, for example: {"F": true, "2.3a": "Bonus"} |

#### Endpoint

```
POST /api/v1/salary/certificate/update.json
```

## Certificate document

The following API endpoints are for managing salary certificate documents. This API is not used to manage salary certificates themselves, but the reading, downloading and mailing of the PDF document.

### Read document

Returns a single document by salary certificate ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the salary certificate. |

#### Endpoint

```
GET /api/v1/salary/certificate/document/read.json
```

### Download PDF

Downloads one or multiple documents in one PDF file.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple salary certificates, comma-separated. |

#### Endpoint

```
GET /api/v1/salary/certificate/document/read.pdf
```

### Download ZIP

Downloads one or multiple documents in a ZIP file (one PDF for each document).

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple salary certificates, comma-separated. |

#### Endpoint

```
GET /api/v1/salary/certificate/document/read.zip
```

### Mail document

Sends a document per e-mail to the desired recipient(s).

#### Parameters

| | | |
| --- | --- | --- |
| `certificateIds` | mandatory, CSV | The IDs of the salary certificates to send as mail, comma-separated. See [Salary certificate](https://app.cashctrl.com/static/help/en/api/index.html#/salary/certificate). |
| `mailFrom` | mandatory, TEXT, MAX:255 | The sender / from e-mail address. |
| `mailSubject` | mandatory, TEXT, MAX:255 | The mail subject. Can contain variables. |
| `mailText` | mandatory, TEXT | The mail text. Can contain variables.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `isCopyToMe` | optional, BOOLEAN | Send a copy to me? (the sender, see `mailFrom`) Possible values: true, false. |
| `mailBcc` | optional, TEXT | The BCC (blind carbon copy) e-mail address. You can enter multiple addresses comma-separated. |
| `mailCc` | optional, TEXT | The CC (carbon copy) e-mail address. You can enter multiple addresses comma-separated. |
| `mailTo` | optional, TEXT | The recipient e-mail address. You can enter multiple addresses comma-separated. Leave empty to use the default e-mail address of the recipient. |

#### Endpoint

```
POST /api/v1/salary/certificate/document/mail.json
```

## Certificate template

The following API endpoints are for managing salary certificate templates. These templates define how the salary certificate form (Form 11 in Switzerland) is filled in.

### Read template

Returns a single template by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the template. |

#### Endpoint

```
GET /api/v1/salary/certificate/template/read.json
```

### List templates

Returns a list of templates.

#### Endpoint

```
GET /api/v1/salary/certificate/template/list.json
```

### List templates as tree

Returns a hierarchical tree of templates.

#### Endpoint

```
GET /api/v1/salary/certificate/template/tree.json
```

### Create template

Creates a new template. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>A name to describe and identify the template.</td></tr>
<tr><th><code>elements</code></th><td>optional, JSON</td><td>List of text/amount elements that will be printed on the form.
<table>
<tr><th><code>code</code></th><td>mandatory, TEXT</td><td>The corresponding form code (e.g. A, B, C, 1, 2, 3, etc.).</td></tr>
<tr><th><code>description</code></th><td>mandatory, TEXT</td><td>A description of this form element.</td></tr>
<tr><th><code>x</code></th><td>mandatory, NUMBER</td><td>The X-coordinate (cm) of the position, where the element will be printed on the form.</td></tr>
<tr><th><code>y</code></th><td>mandatory, NUMBER</td><td>The Y-coordinate (cm) of the position, where the element will be printed on the form.</td></tr>
<tr><th><code>alignment</code></th><td>optional, TEXT</td><td>The alignment of the printed text/value. Defaults to LEFT. Possible values: LEFT, RIGHT.</td></tr>
<tr><th><code>calculation</code></th><td>optional, TEXT</td><td>The numeric value, which will be printed on the form, can be calculated here using math with variables. Leave empty to use the value calculated from the salary type via form code (see <code>code</code>).</td></tr>
<tr><th><code>dataType</code></th><td>optional, TEXT</td><td>The data type of the editable field, if <code>isOverridable</code> is set. Possible values: TEXT, CHECKBOX.</td></tr>
<tr><th><code>fieldInfo</code></th><td>optional, TEXT</td><td>The field info of the editable field, displayed as a tooltip, if <code>isOverridable</code> is set.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Marked as inactive, the element will no longer be printed on the form. Possible values: true, false.</td></tr>
<tr><th><code>isOverridable</code></th><td>optional, BOOLEAN</td><td>Whether the value of this element is editable by the user in the salary certificate's edit dialog. Possible values: true, false.</td></tr>
<tr><th><code>text</code></th><td>optional, TEXT</td><td>Instead of a calculated value (see <code>calculation</code>), we can instead print text.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
</table>
</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>The file containing the salary certificate form. Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>isDefault</code></th><td>optional, BOOLEAN</td><td>Mark the template as the default template to use. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the template as inactive. Inactive templates are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>mailSubject</code></th><td>optional, TEXT, MAX:255</td><td>The mail subject (when sending the salary certificate via e-mail). Can contain variables.</td></tr>
<tr><th><code>mailTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the mail body text (when sending the salary certificate via e-mail).</td></tr>
<tr><th><code>orgLocationId</code></th><td>optional, NUMBER</td><td>The ID of the location (for the organization's address and phone number).</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent template to inherit from. PDF and elements will be inherited from the parent.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/certificate/template/create.json
```

### Update template

Updates an existing template. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the template to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>A name to describe and identify the template.</td></tr>
<tr><th><code>elements</code></th><td>optional, JSON</td><td>List of text/amount elements that will be printed on the form.
<table>
<tr><th><code>code</code></th><td>mandatory, TEXT</td><td>The corresponding form code (e.g. A, B, C, 1, 2, 3, etc.).</td></tr>
<tr><th><code>description</code></th><td>mandatory, TEXT</td><td>A description of this form element.</td></tr>
<tr><th><code>x</code></th><td>mandatory, NUMBER</td><td>The X-coordinate (cm) of the position, where the element will be printed on the form.</td></tr>
<tr><th><code>y</code></th><td>mandatory, NUMBER</td><td>The Y-coordinate (cm) of the position, where the element will be printed on the form.</td></tr>
<tr><th><code>alignment</code></th><td>optional, TEXT</td><td>The alignment of the printed text/value. Defaults to LEFT. Possible values: LEFT, RIGHT.</td></tr>
<tr><th><code>calculation</code></th><td>optional, TEXT</td><td>The numeric value, which will be printed on the form, can be calculated here using math with variables. Leave empty to use the value calculated from the salary type via form code (see <code>code</code>).</td></tr>
<tr><th><code>dataType</code></th><td>optional, TEXT</td><td>The data type of the editable field, if <code>isOverridable</code> is set. Possible values: TEXT, CHECKBOX.</td></tr>
<tr><th><code>fieldInfo</code></th><td>optional, TEXT</td><td>The field info of the editable field, displayed as a tooltip, if <code>isOverridable</code> is set.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Marked as inactive, the element will no longer be printed on the form. Possible values: true, false.</td></tr>
<tr><th><code>isOverridable</code></th><td>optional, BOOLEAN</td><td>Whether the value of this element is editable by the user in the salary certificate's edit dialog. Possible values: true, false.</td></tr>
<tr><th><code>text</code></th><td>optional, TEXT</td><td>Instead of a calculated value (see <code>calculation</code>), we can instead print text.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
</table>
</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>The file containing the salary certificate form. Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>isDefault</code></th><td>optional, BOOLEAN</td><td>Mark the template as the default template to use. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the template as inactive. Inactive templates are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>mailSubject</code></th><td>optional, TEXT, MAX:255</td><td>The mail subject (when sending the salary certificate via e-mail). Can contain variables.</td></tr>
<tr><th><code>mailTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the mail body text (when sending the salary certificate via e-mail).</td></tr>
<tr><th><code>orgLocationId</code></th><td>optional, NUMBER</td><td>The ID of the location (for the organization's address and phone number).</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent template to inherit from. PDF and elements will be inherited from the parent.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/certificate/template/update.json
```

### Delete templates

Deletes one or multiple template. Note that you can only delete templates that aren't used. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/certificate/template/delete.json
```

## Document

The following API endpoints are for managing salary statement documents. This API is not used to manage salary statements themselves, but the reading, downloading and mailing of the PDF document.

### Read document

Returns a single document by salary statement ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the salary statement. |

#### Endpoint

```
GET /api/v1/salary/document/read.json
```

### Download PDF

Downloads one or multiple documents in one PDF file.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple salary statements, comma-separated. |

#### Endpoint

```
GET /api/v1/salary/document/read.pdf
```

### Download ZIP

Downloads one or multiple documents in a ZIP file (one PDF for each document).

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple salary statements, comma-separated. |

#### Endpoint

```
GET /api/v1/salary/document/read.zip
```

### Mail document

Sends a document per e-mail to the desired recipient(s).

#### Parameters

| | | |
| --- | --- | --- |
| `mailFrom` | mandatory, TEXT, MAX:255 | The sender / from e-mail address. |
| `mailSubject` | mandatory, TEXT, MAX:255 | The mail subject. Can contain variables. |
| `mailText` | mandatory, TEXT | The mail text. Can contain variables.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `statementIds` | mandatory, CSV | The IDs of the salary statements to send as mail, comma-separated. See [Salary statement](https://app.cashctrl.com/static/help/en/api/index.html#/salary/statement). |
| `isCopyToMe` | optional, BOOLEAN | Send a copy to me? (the sender, see `mailFrom`) Possible values: true, false. |
| `mailBcc` | optional, TEXT | The BCC (blind carbon copy) e-mail address. You can enter multiple addresses comma-separated. |
| `mailCc` | optional, TEXT | The CC (carbon copy) e-mail address. You can enter multiple addresses comma-separated. |
| `mailTo` | optional, TEXT | The recipient e-mail address. You can enter multiple addresses comma-separated. Leave empty to use the default e-mail address of the recipient. |
| `sentStatusId` | optional, NUMBER | The ID of the status to set on the salary statement after the mail has been sent. See [Salary status](https://app.cashctrl.com/static/help/en/api/index.html#/salary/status). |

#### Endpoint

```
POST /api/v1/salary/document/mail.json
```

### Update document

Updates an existing document. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the salary document to update. See [Salary statement](https://app.cashctrl.com/static/help/en/api/index.html#/salary/statement). |
| `fileId` | optional, NUMBER | An optional PDF document whose pages are added at the end of the salary statement. Supported type: PDF. Max. size: 500KB. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |
| `footer` | optional, HTML | The text displayed below the items list on the document used by default for salary statements.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `header` | optional, HTML | The text displayed above the items list on the document used by default for salary statements.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `layoutId` | optional, NUMBER | The ID of the layout. See [Salary layout](https://app.cashctrl.com/static/help/en/api/index.html#/salary/layout). |
| `orgBankAccountId` | optional, NUMBER | The ID of the organization's bank account. See [Bank account](https://app.cashctrl.com/static/help/en/api/index.html#/account/bank). |
| `orgLocationId` | optional, NUMBER | The ID of the sender location. See [Location](https://app.cashctrl.com/static/help/en/api/index.html#/location). |
| `recipientAddressId` | optional, NUMBER | The ID of the recipient address (person address). See [Person](https://app.cashctrl.com/static/help/en/api/index.html#/person). |
| `recipientBankAccountId` | optional, NUMBER | The ID of the recipient's bank account. |

#### Endpoint

```
POST /api/v1/salary/document/update.json
```

## Field

The following API endpoints are for reading salary fields. Salary fields belong to salary types, so to create or update them, you have to create/update a [Salary type](https://app.cashctrl.com/static/help/en/api/index.html#/salary/type). The endpoints here are only for reading and listing salary fields directly, for convenience.

### Read field

Returns a single field by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the field. |

#### Endpoint

```
GET /api/v1/salary/field/read.json
```

### List fields

Returns a list of fields.

#### Parameters

| | | |
| --- | --- | --- |
| `typeId` | mandatory, NUMBER | The ID of the salary type. |

#### Endpoint

```
GET /api/v1/salary/field/list.json
```

## Insurance type

The following API endpoints are for managing salary insurance types.

### Read insurance type

Returns a single insurance type by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the insurance type. |

#### Endpoint

```
GET /api/v1/salary/insurance/type/read.json
```

### List insurance types

Returns a list of insurance types.

#### Endpoint

```
GET /api/v1/salary/insurance/type/list.json
```

### Create insurance type

Creates a new insurance type. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:40</td><td>The name of the insurance type.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>codes</code></th><td>optional, TEXT</td><td>A list of codes (like A1, A2, etc.).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:10</td><td>Insurance code (like A1, A2, etc.)</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:100</td><td>An optional description.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
</table>
</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:100</td><td>An optional description.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/insurance/type/create.json
```

### Update insurance type

Updates an existing insurance type. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the insurance type to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:40</td><td>The name of the insurance type.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>codes</code></th><td>optional, TEXT</td><td>A list of codes (like A1, A2, etc.).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:10</td><td>Insurance code (like A1, A2, etc.)</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:100</td><td>An optional description.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
</table>
</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:100</td><td>An optional description.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/insurance/type/update.json
```

### Delete insurance types

Deletes one or multiple insurance types. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/insurance/type/delete.json
```

## Layout

The following API endpoints are for managing salary layouts. Layouts define the look and feel of the [Salary document](https://app.cashctrl.com/static/help/en/api/index.html#/salary/document).

### Read layout

Returns a single layout by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/layout/read.json
```

### List layouts

Returns a list of all layouts.

#### Endpoint

```
GET /api/v1/salary/layout/list.json
```

### Create layout

Creates a new layout. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>A name to describe and identify the layout.</td></tr>
<tr><th><code>elements</code></th><td>optional, JSON</td><td>List of elements containing HTML/CSS snippets for the different parts of the layout.
<table>
<tr><th><code>elementId</code></th><td>mandatory, TEXT</td><td>The layout element ID (e.g. <code>HEADER</code>, <code>FOOTER</code>, etc.). Possible values: HEADER, FOOTER, GENERAL, ADDRESS_WINDOW, INFO_TABLE, TEXT_ABOVE, ITEMS_TABLE, SALARY_TABLE, TEXT_BELOW, LEGACY.</td></tr>
<tr><th><code>css</code></th><td>optional, TEXT</td><td>The CSS snippet.</td></tr>
<tr><th><code>html</code></th><td>optional, TEXT</td><td>The HTML snippet.</td></tr>
</table>
</td></tr>
<tr><th><code>footer</code></th><td>optional, HTML</td><td>The footer text, which is displayed at the bottom of the document.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>isCountryEnglish</code></th><td>optional, BOOLEAN</td><td>Display country always in english (UPU standard)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isCountryUppercase</code></th><td>optional, BOOLEAN</td><td>Display country uppercase (UPU standard)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayBase</code></th><td>optional, BOOLEAN</td><td>Display base column? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayDocumentName</code></th><td>optional, BOOLEAN</td><td>Display document name (heading)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayDocumentNr</code></th><td>optional, BOOLEAN</td><td>Display document number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayEmployeeNr</code></th><td>optional, BOOLEAN</td><td>Display employee (person) number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayLogo</code></th><td>optional, BOOLEAN</td><td>Display logo? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayNr</code></th><td>optional, BOOLEAN</td><td>Display salary type number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayOrgAddressInWindow</code></th><td>optional, BOOLEAN</td><td>Display address of your own organization in address window? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPaymentDate</code></th><td>optional, BOOLEAN</td><td>Display payment date? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayQuantity</code></th><td>optional, BOOLEAN</td><td>Display quantity column? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayRate</code></th><td>optional, BOOLEAN</td><td>Display rate column? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplaySsn</code></th><td>optional, BOOLEAN</td><td>Display social security number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the layout as inactive. Inactive layouts are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>isOmitSameCountry</code></th><td>optional, BOOLEAN</td><td>Omit country, if same between sender/recipient? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>letterPaperFileId</code></th><td>optional, NUMBER</td><td>An optional letter paper to embed on every page (behind the text). Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>logoHeight</code></th><td>optional, NUMBER, MIN:0.1, MAX:9.0</td><td>The height of the logo in centimeters.</td></tr>
<tr><th><code>pageSize</code></th><td>optional, TEXT</td><td>The page size of the document. Defaults to A4. Possible values: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, LEGAL, LETTER, A4R.</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent layout to inherit from. Letter paper, HTML and CSS will be inherited from the parent.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/layout/create.json
```

### Update layout

Updates an existing layout. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the layout to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>A name to describe and identify the layout.</td></tr>
<tr><th><code>elements</code></th><td>optional, JSON</td><td>List of elements containing HTML/CSS snippets for the different parts of the layout.
<table>
<tr><th><code>elementId</code></th><td>mandatory, TEXT</td><td>The layout element ID (e.g. <code>HEADER</code>, <code>FOOTER</code>, etc.). Possible values: HEADER, FOOTER, GENERAL, ADDRESS_WINDOW, INFO_TABLE, TEXT_ABOVE, ITEMS_TABLE, SALARY_TABLE, TEXT_BELOW, LEGACY.</td></tr>
<tr><th><code>css</code></th><td>optional, TEXT</td><td>The CSS snippet.</td></tr>
<tr><th><code>html</code></th><td>optional, TEXT</td><td>The HTML snippet.</td></tr>
</table>
</td></tr>
<tr><th><code>footer</code></th><td>optional, HTML</td><td>The footer text, which is displayed at the bottom of the document.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>isCountryEnglish</code></th><td>optional, BOOLEAN</td><td>Display country always in english (UPU standard)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isCountryUppercase</code></th><td>optional, BOOLEAN</td><td>Display country uppercase (UPU standard)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayBase</code></th><td>optional, BOOLEAN</td><td>Display base column? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayDocumentName</code></th><td>optional, BOOLEAN</td><td>Display document name (heading)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayDocumentNr</code></th><td>optional, BOOLEAN</td><td>Display document number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayEmployeeNr</code></th><td>optional, BOOLEAN</td><td>Display employee (person) number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayLogo</code></th><td>optional, BOOLEAN</td><td>Display logo? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayNr</code></th><td>optional, BOOLEAN</td><td>Display salary type number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayOrgAddressInWindow</code></th><td>optional, BOOLEAN</td><td>Display address of your own organization in address window? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPaymentDate</code></th><td>optional, BOOLEAN</td><td>Display payment date? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayQuantity</code></th><td>optional, BOOLEAN</td><td>Display quantity column? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayRate</code></th><td>optional, BOOLEAN</td><td>Display rate column? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplaySsn</code></th><td>optional, BOOLEAN</td><td>Display social security number? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the layout as inactive. Inactive layouts are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>isOmitSameCountry</code></th><td>optional, BOOLEAN</td><td>Omit country, if same between sender/recipient? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>letterPaperFileId</code></th><td>optional, NUMBER</td><td>An optional letter paper to embed on every page (behind the text). Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>logoHeight</code></th><td>optional, NUMBER, MIN:0.1, MAX:9.0</td><td>The height of the logo in centimeters.</td></tr>
<tr><th><code>pageSize</code></th><td>optional, TEXT</td><td>The page size of the document. Defaults to A4. Possible values: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, LEGAL, LETTER, A4R.</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent layout to inherit from. Letter paper, HTML and CSS will be inherited from the parent.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/layout/update.json
```

### Delete layouts

Deletes one or multiple layouts. Note that you cannot delete system layouts, only manually created ones. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/layout/delete.json
```

## Payment

The following API endpoints are for creating and downloading payment orders. Note that this does not create any book entries, for that see [Book entries](https://app.cashctrl.com/static/help/en/api/index.html#/salary/bookentry). Here we are either creating an ISO 20022 pain.001 file or a PDF to download. The pain.001 file can be used in e-banking to automatically process multiple payments. Please first use the Create endpoint (don't skip this!), and then the Download endpoint.

### Create payment

Creates a new payment. This must first be executed before downloading the pain.001 or PDF file with the next endpoint, otherwise we won't be able to match the payments from a camt.052/053/054 file later on. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `date` | mandatory, DATE | The execution date for the payment.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `statementIds` | mandatory, CSV | The IDs of the selected salary statements, comma-separated. |
| `amount` | optional, NUMBER | A partial payment amount per salary statement. Leave empty to pay all open amounts. |
| `isCombine` | optional, BOOLEAN | If set, merges multiple payments to the same payee into one transaction. Possible values: true, false. |
| `statusId` | optional, NUMBER | The ID of the new status for the salary statement. |
| `type` | optional, TEXT | The type of payment and file to generate. Defaults to PAIN (pain.001). Possible values: PAIN, SEPA_PAIN, WIRE_PDF, CASH_PDF. |

#### Endpoint

```
POST /api/v1/salary/payment/create.json
```

### Download file

Downloads the pain.001 or PDF file. Please use the create endpoint first, and then use the same parameters to download the file here. Returns a file.

#### Parameters

| | | |
| --- | --- | --- |
| `date` | mandatory, DATE | The execution date for the payment.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `statementIds` | mandatory, CSV | The IDs of the selected salary statements, comma-separated. |
| `amount` | optional, NUMBER | A partial payment amount per salary statement. Leave empty to pay all open amounts. |
| `isCombine` | optional, BOOLEAN | If set, merges multiple payments to the same payee into one transaction. Possible values: true, false. |
| `statusId` | optional, NUMBER | The ID of the new status for the salary statement. |
| `type` | optional, TEXT | The type of payment and file to generate. Defaults to PAIN (pain.001). Possible values: PAIN, SEPA_PAIN, WIRE_PDF, CASH_PDF. |

#### Endpoint

```
GET /api/v1/salary/payment/download
```

## Setting

The following API endpoints are for managing salary settings (global values). This is a list of global values that can be accessed via variable (e.g. $myGlobalValue) in salary formulas, for example in the calculation of a salary type or pre-calculation within a salary type. Can also be displayed as a column in certain salary reports, or used in the calculation of a custom column.

### Read setting

Returns a single setting by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/setting/read.json
```

### List settings

Returns a list of all settings.

#### Endpoint

```
GET /api/v1/salary/setting/list.json
```

### Create setting

Creates a new setting. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:100 | The name of the setting.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `variableName` | mandatory, TEXT, MIN:2, MAX:32 | The variable name used in calculations. Must start with `$` and contain only alphanumeric characters. |
| `boolValue` | optional, BOOLEAN | The boolean value (if type is `BOOLEAN`, ignored otherwise). Possible values: true, false. |
| `decimalValue` | optional, NUMBER | The decimal value (if type is `DECIMAL`, ignored otherwise). |
| `isPercentage` | optional, BOOLEAN | Whether the decimal value is a percentage or not (if type is `DECIMAL`, ignored otherwise). Possible values: true, false. |
| `textValue` | optional, TEXT, MAX:255 | The text value (if type is `TEXT`, ignored otherwise). |
| `type` | optional, TEXT | The data type of the setting. Possible values: TEXT, BOOLEAN, DECIMAL. |

#### Endpoint

```
POST /api/v1/salary/setting/create.json
```

### Update setting

Updates an existing setting. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the setting to update. |
| `name` | mandatory, TEXT, MAX:100 | The name of the setting.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `variableName` | mandatory, TEXT, MIN:2, MAX:32 | The variable name used in calculations. Must start with `$` and contain only alphanumeric characters. |
| `boolValue` | optional, BOOLEAN | The boolean value (if type is `BOOLEAN`, ignored otherwise). Possible values: true, false. |
| `decimalValue` | optional, NUMBER | The decimal value (if type is `DECIMAL`, ignored otherwise). |
| `isPercentage` | optional, BOOLEAN | Whether the decimal value is a percentage or not (if type is `DECIMAL`, ignored otherwise). Possible values: true, false. |
| `textValue` | optional, TEXT, MAX:255 | The text value (if type is `TEXT`, ignored otherwise). |
| `type` | optional, TEXT | The data type of the setting. Possible values: TEXT, BOOLEAN, DECIMAL. |

#### Endpoint

```
POST /api/v1/salary/setting/update.json
```

### Delete settings

Deletes one or multiple settings. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/setting/delete.json
```

## Statement

The following API endpoints are for managing salary statements.

### Read statement

Returns a single statement by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/statement/read.json
```

### List statements

Returns a list of statements.

#### Parameters

<table>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open salary statements (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary statements that are overdue (past the payment date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/statement/list.json
```

### Export to Excel

Returns an Excel file of the statements list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open salary statements (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary statements that are overdue (past the payment date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/statement/list.xlsx
```

### Export to CSV

Returns a CSV file of the statements list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open salary statements (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary statements that are overdue (past the payment date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/statement/list.csv
```

### Export to PDF

Returns a PDF file of the statements list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the entries.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open salary statements (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary statements that are overdue (past the payment date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>Optional ID of an employee to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/statement/list.pdf
```

### Create statement

Creates a new statement. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>date</code></th><td>mandatory, DATE</td><td>The date of the salary statement.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>datePayment</code></th><td>mandatory, DATE</td><td>The date of payment.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>personId</code></th><td>mandatory, NUMBER</td><td>The ID of the person (employee).</td></tr>
<tr><th><code>statusId</code></th><td>mandatory, NUMBER</td><td>The ID of the current status.</td></tr>
<tr><th><code>templateId</code></th><td>mandatory, NUMBER</td><td>The ID of the template.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next salary statement will be created X days before the start date. Leave empty or set to 0 to have the next salary statement created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence (see <code>recurrence</code> parameter). Salary statements repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>insurances</code></th><td>optional, JSON</td><td>List of insurances. Whether an insurance is mandatory or not depends on the used salary types (see <code>types</code>). Each salary type defines the type of insurance required.
<table>
<tr><th><code>contractId</code></th><td>mandatory, NUMBER</td><td>The ID of the insurance contract. Insurance providers are entered as persons, and each insurance provider can have multiple insurance contracts. A contract consists of an insurance type (e.g. AHV/IV/EO/ALV, BVG, UVG, etc.) and a contract number and, if applicable, a sub number. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>codeId</code></th><td>optional, NUMBER</td><td>The ID of the insurance code (e.g. A1, A2, B1, etc.), if applicable. Each insurance type can have multiple codes. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/insurance/type">Insurance type</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>message</code></th><td>optional, TEXT, MAX:50</td><td>A message for the payment recipient (included in the pain xml file).</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether to send a notification e-mail when salary statements have been created or not. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The salary statement number (e.g. 'LA-202401201'). Leave empty to generate the number with <code>sequenceNumberId</code>. This becomes mandatory if a sequence number is set neither here nor in the template.</td></tr>
<tr><th><code>recalculate</code></th><td>optional, BOOLEAN</td><td>If <code>id</code> is set, values are not recalculated by default. Set this to true to have them recalculated. Possible values: true, false.</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the salary statement should be automatically repeated. Leave empty to not repeat the salary statement. See also <code>startDate</code> and <code>endDate</code>. Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the salary statement number (see <code>nr</code>). If empty, the sequence number of the template is used (if set). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence (see <code>recurrence</code> parameter). This is the date when the salary statement will be repeated next.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>types</code></th><td>optional, JSON</td><td>The list of salary types.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateEnd</code></th><td>optional, DATE</td><td>Optional end date for when this salary type becomes inactive (active otherwise). See also <code>dateStart</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateStart</code></th><td>optional, DATE</td><td>Optional start date for when this salary type becomes active (inactive otherwise). See also <code>dateEnd</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary template or type.</td></tr>
</table>
</td></tr>
<tr><th><code>valuesLocal</code></th><td>optional, JSON</td><td>A JSON object containing each salary type's field values. This is a simple key/value pair map (the key being the variable name).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/statement/create.json
```

### Update statement

Updates an existing statement. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>date</code></th><td>mandatory, DATE</td><td>The date of the salary statement.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>datePayment</code></th><td>mandatory, DATE</td><td>The date of payment.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the salary statement to update.</td></tr>
<tr><th><code>personId</code></th><td>mandatory, NUMBER</td><td>The ID of the person (employee).</td></tr>
<tr><th><code>statusId</code></th><td>mandatory, NUMBER</td><td>The ID of the current status.</td></tr>
<tr><th><code>templateId</code></th><td>mandatory, NUMBER</td><td>The ID of the template.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next salary statement will be created X days before the start date. Leave empty or set to 0 to have the next salary statement created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence (see <code>recurrence</code> parameter). Salary statements repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>insurances</code></th><td>optional, JSON</td><td>List of insurances. Whether an insurance is mandatory or not depends on the used salary types (see <code>types</code>). Each salary type defines the type of insurance required.
<table>
<tr><th><code>contractId</code></th><td>mandatory, NUMBER</td><td>The ID of the insurance contract. Insurance providers are entered as persons, and each insurance provider can have multiple insurance contracts. A contract consists of an insurance type (e.g. AHV/IV/EO/ALV, BVG, UVG, etc.) and a contract number and, if applicable, a sub number. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>codeId</code></th><td>optional, NUMBER</td><td>The ID of the insurance code (e.g. A1, A2, B1, etc.), if applicable. Each insurance type can have multiple codes. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/insurance/type">Insurance type</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>message</code></th><td>optional, TEXT, MAX:50</td><td>A message for the payment recipient (included in the pain xml file).</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether to send a notification e-mail when salary statements have been created or not. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The salary statement number (e.g. 'LA-202401201'). Leave empty to generate the number with <code>sequenceNumberId</code>. This becomes mandatory if a sequence number is set neither here nor in the template.</td></tr>
<tr><th><code>recalculate</code></th><td>optional, BOOLEAN</td><td>If <code>id</code> is set, values are not recalculated by default. Set this to true to have them recalculated. Possible values: true, false.</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the salary statement should be automatically repeated. Leave empty to not repeat the salary statement. See also <code>startDate</code> and <code>endDate</code>. Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the salary statement number (see <code>nr</code>). If empty, the sequence number of the template is used (if set). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence (see <code>recurrence</code> parameter). This is the date when the salary statement will be repeated next.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>types</code></th><td>optional, JSON</td><td>The list of salary types.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateEnd</code></th><td>optional, DATE</td><td>Optional end date for when this salary type becomes inactive (active otherwise). See also <code>dateStart</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateStart</code></th><td>optional, DATE</td><td>Optional start date for when this salary type becomes active (inactive otherwise). See also <code>dateEnd</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary template or type.</td></tr>
</table>
</td></tr>
<tr><th><code>valuesLocal</code></th><td>optional, JSON</td><td>A JSON object containing each salary type's field values. This is a simple key/value pair map (the key being the variable name).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/statement/update.json
```

### Update multiple

Updates multiple existing statements. Note that you can omit parameters that you don't want to modify, the values will not be touched. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>ids</code></th><td>mandatory, CSV</td><td>The IDs of the salary statements, comma-separated.</td></tr>
<tr><th><code>attachments</code></th><td>optional, TEXT</td><td>List of file attachments (overrides existing attachments).
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>New values for custom fields.</td></tr>
<tr><th><code>date</code></th><td>optional, TEXT</td><td>The new date of the salary statement.</td></tr>
<tr><th><code>datePayment</code></th><td>optional, TEXT</td><td>The new date of payment.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next salary statement will be created X days before the start date. Leave empty or set to 0 to have the next salary statement created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence (see <code>recurrence</code> parameter). Salary statements repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>insurancesToAdd</code></th><td>optional, JSON</td><td>List of insurances to add.
<table>
<tr><th><code>contractId</code></th><td>mandatory, NUMBER</td><td>The ID of the insurance contract. Insurance providers are entered as persons, and each insurance provider can have multiple insurance contracts. A contract consists of an insurance type (e.g. AHV/IV/EO/ALV, BVG, UVG, etc.) and a contract number and, if applicable, a sub number. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>codeId</code></th><td>optional, NUMBER</td><td>The ID of the insurance code (e.g. A1, A2, B1, etc.), if applicable. Each insurance type can have multiple codes. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/insurance/type">Insurance type</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>insurancesToRemove</code></th><td>optional, JSON</td><td>List of insurances to remove.
<table>
<tr><th><code>contractId</code></th><td>mandatory, NUMBER</td><td>The ID of the insurance contract. Insurance providers are entered as persons, and each insurance provider can have multiple insurance contracts. A contract consists of an insurance type (e.g. AHV/IV/EO/ALV, BVG, UVG, etc.) and a contract number and, if applicable, a sub number. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>codeId</code></th><td>optional, NUMBER</td><td>The ID of the insurance code (e.g. A1, A2, B1, etc.), if applicable. Each insurance type can have multiple codes. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/insurance/type">Insurance type</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>The new notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether to send a notification e-mail when salary statements have been created or not. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>personId</code></th><td>optional, TEXT</td><td>The ID of the new person (employee).</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the salary statement should be automatically repeated. Leave empty to not repeat the salary statement. See also <code>startDate</code> and <code>endDate</code>. Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence (see <code>recurrence</code> parameter). This is the date when the salary statement will be repeated next.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>statusId</code></th><td>optional, TEXT</td><td>The ID of the new status.</td></tr>
<tr><th><code>templateId</code></th><td>optional, TEXT</td><td>The ID of the new template.</td></tr>
<tr><th><code>typesToAdd</code></th><td>optional, JSON</td><td>List of salary types to add or overwrite.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateEnd</code></th><td>optional, DATE</td><td>Optional end date for when this salary type becomes inactive (active otherwise). See also <code>dateStart</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateStart</code></th><td>optional, DATE</td><td>Optional start date for when this salary type becomes active (inactive otherwise). See also <code>dateEnd</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary template or type.</td></tr>
</table>
</td></tr>
<tr><th><code>typesToRemove</code></th><td>optional, JSON</td><td>List of salary types to remove.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateEnd</code></th><td>optional, DATE</td><td>Optional end date for when this salary type becomes inactive (active otherwise). See also <code>dateStart</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateStart</code></th><td>optional, DATE</td><td>Optional start date for when this salary type becomes active (inactive otherwise). See also <code>dateEnd</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary template or type.</td></tr>
</table>
</td></tr>
<tr><th><code>valuesLocal</code></th><td>optional, JSON</td><td>A JSON object containing each salary type's field values. This is a simple key/value pair map (the key being the variable name).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/statement/update_multiple.json
```

### Update status

Updates the status of an existing statement by statement ID. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple salary statements, comma-separated. |
| `statusId` | mandatory, NUMBER | The ID of the new status. |

#### Endpoint

```
POST /api/v1/salary/statement/update_status.json
```

### Update recurrence

Updates the recurrence of an existing statement by statement ID. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the salary statement. |
| `daysBefore` | optional, NUMBER | The next salary statement will be created X days before the start date. Leave empty or set to 0 to have the next salary statement created on the start date itself. See `recurrence` parameter. |
| `endDate` | optional, DATE | The end date for the recurrence. Salary statements repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `notifyEmail` | optional, TEXT | The e-mail address to send a notification to. See `notifyType` parameter. |
| `notifyPersonId` | optional, NUMBER | The ID of the person to send a notification to. See `notifyType` parameter. |
| `notifyType` | optional, TEXT | Whether or not to send a notification e-mail when salary statements have been created. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL. |
| `notifyUserId` | optional, NUMBER | The ID of the user to send a notification to. See `notifyType` parameter. Note: User must be in this organization. |
| `recurrence` | optional, TEXT | The interval of how often the salary statement should be automatically repeated. Leave empty to not repeat the salary statement (or to remove recurrence). Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY. |
| `startDate` | optional, DATE | The start date for the recurrence. This is the date when the salary statement will be repeated next.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
POST /api/v1/salary/statement/update_recurrence.json
```

### Delete statements

Deletes one or multiple statements. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/statement/delete.json
```

### Calculate

Calculates all of the values and items on a salary statement using the formulas from salary types and pre-calculations.

#### Parameters

<table>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values.</td></tr>
<tr><th><code>date</code></th><td>optional, DATE</td><td>The date of the salary statement.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>datePayment</code></th><td>optional, DATE</td><td>The payment date of the salary statement.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>id</code></th><td>optional, NUMBER</td><td>Optional ID of the existing salary statement.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>The ID of the employee. <code>isEmployee</code> must be true on the person object.</td></tr>
<tr><th><code>recalculate</code></th><td>optional, BOOLEAN</td><td>If <code>id</code> is set, values are not recalculated by default. Set this to true to have them recalculated. Possible values: true, false.</td></tr>
<tr><th><code>templateId</code></th><td>optional, NUMBER</td><td>The salary template to inherit values from. Those values are overriden by <code>valuesLocal</code>.</td></tr>
<tr><th><code>types</code></th><td>optional, JSON</td><td>The salary types to calculate the values for. All other salary types won't be calculated.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateEnd</code></th><td>optional, DATE</td><td>Optional end date for when this salary type becomes inactive (active otherwise). See also <code>dateStart</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>dateStart</code></th><td>optional, DATE</td><td>Optional start date for when this salary type becomes active (inactive otherwise). See also <code>dateEnd</code>.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary template or type.</td></tr>
</table>
</td></tr>
<tr><th><code>valuesLocal</code></th><td>optional, TEXT</td><td>The values set directly on the salary statement, used for calculation.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/statement/calculate.json
```

### Update attachments

Updates the file attachments of an salary statement. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/salary/statement/update_attachments.json
```

## Status

The following API endpoints are for managing the salary status list.

### Read status

Returns a single status by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/status/read.json
```

### List status

Returns a list of status.

#### Endpoint

```
GET /api/v1/salary/status/list.json
```

### Create status

Creates a new status. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `icon` | mandatory, TEXT | The icon/color of the status. Possible values: BLUE, GREEN, RED, YELLOW, ORANGE, BLACK, GRAY, BROWN, VIOLET, PINK. |
| `name` | mandatory, TEXT, MAX:40 | The name of the status.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `actionId` | optional, TEXT | An action associated with the status, i.e. what happens after I change the status to this? Possible values: CREATE_PAYMENT_ORDER, BOOK_PAYMENT, SEND_MAIL. |
| `isBook` | optional, BOOLEAN | Whether journal book entries will be created with this status. For example, the status 'Draft' will not create any book entries, but all the other statuses after that ('Open', 'Paid', etc.) will. Defaults to false. Possible values: true, false. |
| `isClosed` | optional, BOOLEAN | Whether the status closes / completes the salary statement. This would be the case, for example, if the salary has been fully paid. The effect is that the salary is no longer due, even if past the due date (so no longer marked red). Defaults to false. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/salary/status/create.json
```

### Update status

Updates an existing status. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `icon` | mandatory, TEXT | The icon/color of the status. Possible values: BLUE, GREEN, RED, YELLOW, ORANGE, BLACK, GRAY, BROWN, VIOLET, PINK. |
| `id` | mandatory, NUMBER | The ID of the status to update. |
| `name` | mandatory, TEXT, MAX:40 | The name of the status.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `actionId` | optional, TEXT | An action associated with the status, i.e. what happens after I change the status to this? Possible values: CREATE_PAYMENT_ORDER, BOOK_PAYMENT, SEND_MAIL. |
| `isBook` | optional, BOOLEAN | Whether journal book entries will be created with this status. For example, the status 'Draft' will not create any book entries, but all the other statuses after that ('Open', 'Paid', etc.) will. Defaults to false. Possible values: true, false. |
| `isClosed` | optional, BOOLEAN | Whether the status closes / completes the salary statement. This would be the case, for example, if the salary has been fully paid. The effect is that the salary is no longer due, even if past the due date (so no longer marked red). Defaults to false. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/salary/status/update.json
```

### Delete status

Deletes one or multiple status. Note that you cannot delete a status that is used. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/status/delete.json
```

### Reorder status

Changes the order of one or multiple status. This is the order in which the status are displayed. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to reorder, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target entry. The entries (see `ids`) will be ordered before or after (see `before`) this entry. |
| `before` | optional, BOOLEAN | Reorder before the target entry, after otherwise. Defaults to true. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/salary/status/reorder.json
```

## Sum

The following API endpoints are for managing salary sums.

### Read sum

Returns a single sum by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/sum/read.json
```

### List sums

Returns a list of sums.

#### Endpoint

```
GET /api/v1/salary/sum/list.json
```

### Create sum

Creates a new sum. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:100 | The name of the sum.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `variableName` | mandatory, TEXT, MAX:32 | The variable name used in calculations. Must start with `$` and contain only alphanumeric characters. |
| `isDisplayColumn` | optional, BOOLEAN | Display this sum as a column in the salary type master report by default? Possible values: true, false. |
| `number` | optional, TEXT, MAX:20 | An optional number, for sorting. |

#### Endpoint

```
POST /api/v1/salary/sum/create.json
```

### Update sum

Updates an existing sum. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the sum to update. |
| `name` | mandatory, TEXT, MAX:100 | The name of the sum.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `variableName` | mandatory, TEXT, MAX:32 | The variable name used in calculations. Must start with `$` and contain only alphanumeric characters. |
| `isDisplayColumn` | optional, BOOLEAN | Display this sum as a column in the salary type master report by default? Possible values: true, false. |
| `number` | optional, TEXT, MAX:20 | An optional number, for sorting. |

#### Endpoint

```
POST /api/v1/salary/sum/update.json
```

### Delete sum

Deletes one or multiple sums. Note that you cannot delete system sums. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/sum/delete.json
```

## Template

The following API endpoints are for managing salary templates. They are templates for salary statements, where you can pre-configure salary types, insurances and values. Templates are hierarchical and inherit all of their properties, salary types, insurances and values from their parent. Salary statements must use a template, so at least one template must exist.

### Read template

Returns a single template by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/template/read.json
```

### List templates

Returns a list of templates.

#### Endpoint

```
GET /api/v1/salary/template/list.json
```

### List templates as tree

Returns a hierarchical tree of templates.

#### Endpoint

```
GET /api/v1/salary/template/tree.json
```

### Create template

Creates a new template. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>A name to describe and identify the template.</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency to use in salary statements.</td></tr>
<tr><th><code>dayOfMonth</code></th><td>optional, NUMBER, MIN:1.0, MAX:31.0</td><td>The day of month used for generating the salary statement date. Leave empty to use today instead.</td></tr>
<tr><th><code>footerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the text below the table (on the salary statement PDF).</td></tr>
<tr><th><code>headerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the text above the table (on the salary statement PDF).</td></tr>
<tr><th><code>insurances</code></th><td>optional, JSON</td><td>List of insurances defined in this template.</td></tr>
<tr><th><code>isDefault</code></th><td>optional, BOOLEAN</td><td>Mark the template as the default template to use. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the template as inactive. Inactive templates are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>layoutId</code></th><td>optional, NUMBER</td><td>The ID of the layout for the salary statement PDF.</td></tr>
<tr><th><code>mailSubject</code></th><td>optional, TEXT, MAX:255</td><td>The mail subject (when sending the salary statement via e-mail). Can contain variables.</td></tr>
<tr><th><code>mailTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the mail body text (when sending the salary statement via e-mail).</td></tr>
<tr><th><code>message</code></th><td>optional, TEXT, MAX:50</td><td>A message for the payment recipient (included in the pain.001 xml file).</td></tr>
<tr><th><code>orgLocationId</code></th><td>optional, NUMBER</td><td>The ID of your organization's location.</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent template to inherit from.</td></tr>
<tr><th><code>paymentDayOfMonth</code></th><td>optional, NUMBER, MIN:1.0, MAX:31.0</td><td>The day of month used for generating the salary statement payment date. Leave empty to use today instead.</td></tr>
<tr><th><code>sequenceNrId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used for salary statements using this template. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>types</code></th><td>optional, JSON</td><td>List of salary types defined in this template.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. Leave empty to inherit the account from the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. Leave empty to inherit the account from the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description. Leave empty to inherit the description from the salary type.</td></tr>
<tr><th><code>isPreConfig</code></th><td>optional, BOOLEAN</td><td>Is pre-configuration? If so, only the values of the salary type are configured here, and the salary type is not automatically added to the salary statement. Otherwise, when selecting this template, the salary type is added. Possible values: true, false.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary type.</td></tr>
</table>
</td></tr>
<tr><th><code>valuesLocal</code></th><td>optional, JSON</td><td>A JSON object containing each salary type's field values. This is a simple key/value pair map (the key being the variable name).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/template/create.json
```

### Update template

Updates an existing template. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the template to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>A name to describe and identify the template.</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency to use in salary statements.</td></tr>
<tr><th><code>dayOfMonth</code></th><td>optional, NUMBER, MIN:1.0, MAX:31.0</td><td>The day of month used for generating the salary statement date. Leave empty to use today instead.</td></tr>
<tr><th><code>footerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the text below the table (on the salary statement PDF).</td></tr>
<tr><th><code>headerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the text above the table (on the salary statement PDF).</td></tr>
<tr><th><code>insurances</code></th><td>optional, JSON</td><td>List of insurances defined in this template.</td></tr>
<tr><th><code>isDefault</code></th><td>optional, BOOLEAN</td><td>Mark the template as the default template to use. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the template as inactive. Inactive templates are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>layoutId</code></th><td>optional, NUMBER</td><td>The ID of the layout for the salary statement PDF.</td></tr>
<tr><th><code>mailSubject</code></th><td>optional, TEXT, MAX:255</td><td>The mail subject (when sending the salary statement via e-mail). Can contain variables.</td></tr>
<tr><th><code>mailTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the text template for the mail body text (when sending the salary statement via e-mail).</td></tr>
<tr><th><code>message</code></th><td>optional, TEXT, MAX:50</td><td>A message for the payment recipient (included in the pain.001 xml file).</td></tr>
<tr><th><code>orgLocationId</code></th><td>optional, NUMBER</td><td>The ID of your organization's location.</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent template to inherit from.</td></tr>
<tr><th><code>paymentDayOfMonth</code></th><td>optional, NUMBER, MIN:1.0, MAX:31.0</td><td>The day of month used for generating the salary statement payment date. Leave empty to use today instead.</td></tr>
<tr><th><code>sequenceNrId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used for salary statements using this template. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>types</code></th><td>optional, JSON</td><td>List of salary types defined in this template.
<table>
<tr><th><code>typeId</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/type">Salary type</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the account on the credit side. Leave empty to inherit the account from the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the account on the debit side. Leave empty to inherit the account from the salary type. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>An optional description. Leave empty to inherit the description from the salary type.</td></tr>
<tr><th><code>isPreConfig</code></th><td>optional, BOOLEAN</td><td>Is pre-configuration? If so, only the values of the salary type are configured here, and the salary type is not automatically added to the salary statement. Otherwise, when selecting this template, the salary type is added. Possible values: true, false.</td></tr>
<tr><th><code>onlyMonth</code></th><td>optional, NUMBER</td><td>Set the number of the month (january = 1) for when this salary type becomes active (inactive otherwise).</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT</td><td>The name as it appears on the salary statement. Leave empty to inherit the name from the salary type.</td></tr>
</table>
</td></tr>
<tr><th><code>valuesLocal</code></th><td>optional, JSON</td><td>A JSON object containing each salary type's field values. This is a simple key/value pair map (the key being the variable name).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/template/update.json
```

### Delete templates

Deletes one or multiple existing templates. Note that you cannot delete a template that is used or has children. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/template/delete.json
```

## Type

The following API endpoints are for managing salary types. Salary types are used in salary [templates](https://app.cashctrl.com/static/help/en/api/index.html#/salary/template) and [statements](https://app.cashctrl.com/static/help/en/api/index.html#/salary/statement) to calculate the items on the salary statement. They can contain input fields and pre-calculations to help calculate their returned value. In the calculation of a salary type you have access to all previous (meaning: lower number) salary type values and their input field values and pre-calculation values, as well as [global values](https://app.cashctrl.com/static/help/en/api/index.html#/salary/setting) via variables (e.g. $myVariable). Also, salary types are [categorized](https://app.cashctrl.com/static/help/en/api/index.html#/salary/category).

### Read type

Returns a single type by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/salary/type/read.json
```

### List types

Returns a list of types.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active salary types. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyChildren</code></th><td>optional, BOOLEAN</td><td>Only include direct children of the category (without grandchildren). See <code>categoryId</code>. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/type/list.json
```

### Export to Excel

Returns an Excel file of the types list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active salary types. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyChildren</code></th><td>optional, BOOLEAN</td><td>Only include direct children of the category (without grandchildren). See <code>categoryId</code>. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/type/list.xlsx
```

### Export to CSV

Returns a CSV file of the types list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active salary types. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyChildren</code></th><td>optional, BOOLEAN</td><td>Only include direct children of the category (without grandchildren). See <code>categoryId</code>. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/type/list.csv
```

### Export to PDF

Returns a PDF file of the types list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active salary types. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyChildren</code></th><td>optional, BOOLEAN</td><td>Only include direct children of the category (without grandchildren). See <code>categoryId</code>. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/salary/type/list.pdf
```

### Create type

Creates a new type. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>mandatory, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/category">Salary category</a>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the salary type.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>number</code></th><td>mandatory, TEXT, MAX:20</td><td>The salary type number.</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of the type ;-) Is the amount of the salary type added or subtracted? Possible values: ADDITION, SUBTRACTION.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>base</code></th><td>optional, TEXT, MAX:32</td><td>The base amount, for display purposes only, not used for calculation. Is displayed on the salary statement.</td></tr>
<tr><th><code>calculation</code></th><td>optional, TEXT</td><td>The amount of the salary statement is calculated here. Can contain a formula with limited JavaScript code.</td></tr>
<tr><th><code>certificateCode</code></th><td>optional, TEXT, MAX:10</td><td>The salary certificate code to add the result of this salary type to.</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the financial account on the credit side. This account will be used to generate the book entries.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the financial account on the debit side. This account will be used to generate the book entries.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:512</td><td>An optional longer description of the salary type.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>fields</code></th><td>optional, JSON</td><td>Form fields for entering data in salary statements or templates, which is used in this salary type's <code>calculation</code>. Similar to custom fields. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a>.</td></tr>
<tr><th><code>insuranceTypeId</code></th><td>optional, NUMBER</td><td>The ID of the corresponding insurance type.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>An inactive salary type is no longer used and won't be available for use in a salary template or statement. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isSchedulable</code></th><td>optional, BOOLEAN</td><td>Whether the salary type can be scheduled (active between start/end date in the salary statement) or not. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isVisible</code></th><td>optional, BOOLEAN</td><td>A visible salary type is displayed on the salary statement, hidden otherwise. Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>preCalculations</code></th><td>optional, JSON</td><td>Pre-calculations that are each stored in a variable, which can be used in the salary type's main <code>calculation</code>.</td></tr>
<tr><th><code>quantity</code></th><td>optional, TEXT, MAX:32</td><td>The quantity, for display purposes only, not used for calculation. Is displayed on the salary statement.</td></tr>
<tr><th><code>rate</code></th><td>optional, TEXT, MAX:32</td><td>The rate (percentage), for display purposes only, not used for calculation. Is displayed on the salary statement.</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT, MAX:100</td><td>The name of the salary type displayed on the salary statement (row name). Leave empty to use the <code>name</code>.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>sums</code></th><td>optional, JSON</td><td>Include the salary type in the following sums.</td></tr>
<tr><th><code>variableName</code></th><td>optional, TEXT, MIN:2, MAX:32</td><td>The name of the variable, in which the result of the <code>calculation</code> will be stored for further calculations in other salary types. The variable must start with a <code>$</code> and contain only alphanumeric characters (a-z, 0-9).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/type/create.json
```

### Update type

Updates an existing type. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>mandatory, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/category">Salary category</a>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the salary type to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the salary type.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>number</code></th><td>mandatory, TEXT, MAX:20</td><td>The salary type number.</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of the type ;-) Is the amount of the salary type added or subtracted? Possible values: ADDITION, SUBTRACTION.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>base</code></th><td>optional, TEXT, MAX:32</td><td>The base amount, for display purposes only, not used for calculation. Is displayed on the salary statement.</td></tr>
<tr><th><code>calculation</code></th><td>optional, TEXT</td><td>The amount of the salary statement is calculated here. Can contain a formula with limited JavaScript code.</td></tr>
<tr><th><code>certificateCode</code></th><td>optional, TEXT, MAX:10</td><td>The salary certificate code to add the result of this salary type to.</td></tr>
<tr><th><code>creditId</code></th><td>optional, NUMBER</td><td>The ID of the financial account on the credit side. This account will be used to generate the book entries.</td></tr>
<tr><th><code>debitId</code></th><td>optional, NUMBER</td><td>The ID of the financial account on the debit side. This account will be used to generate the book entries.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:512</td><td>An optional longer description of the salary type.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>fields</code></th><td>optional, JSON</td><td>Form fields for entering data in salary statements or templates, which is used in this salary type's <code>calculation</code>. Similar to custom fields. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a>.</td></tr>
<tr><th><code>insuranceTypeId</code></th><td>optional, NUMBER</td><td>The ID of the corresponding insurance type.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>An inactive salary type is no longer used and won't be available for use in a salary template or statement. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isSchedulable</code></th><td>optional, BOOLEAN</td><td>Whether the salary type can be scheduled (active between start/end date in the salary statement) or not. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isVisible</code></th><td>optional, BOOLEAN</td><td>A visible salary type is displayed on the salary statement, hidden otherwise. Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>preCalculations</code></th><td>optional, JSON</td><td>Pre-calculations that are each stored in a variable, which can be used in the salary type's main <code>calculation</code>.</td></tr>
<tr><th><code>quantity</code></th><td>optional, TEXT, MAX:32</td><td>The quantity, for display purposes only, not used for calculation. Is displayed on the salary statement.</td></tr>
<tr><th><code>rate</code></th><td>optional, TEXT, MAX:32</td><td>The rate (percentage), for display purposes only, not used for calculation. Is displayed on the salary statement.</td></tr>
<tr><th><code>rowName</code></th><td>optional, TEXT, MAX:100</td><td>The name of the salary type displayed on the salary statement (row name). Leave empty to use the <code>name</code>.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>sums</code></th><td>optional, JSON</td><td>Include the salary type in the following sums.</td></tr>
<tr><th><code>variableName</code></th><td>optional, TEXT, MIN:2, MAX:32</td><td>The name of the variable, in which the result of the <code>calculation</code> will be stored for further calculations in other salary types. The variable must start with a <code>$</code> and contain only alphanumeric characters (a-z, 0-9).</td></tr>
</table>

#### Endpoint

```
POST /api/v1/salary/type/update.json
```

### Categorize types

Assigns one or multiple types to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/salary/type/categorize.json
```

### Delete types

Deletes one or multiple types. Note that you can only delete types that aren't used. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/salary/type/delete.json
```
