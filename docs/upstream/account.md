Source: <https://app.cashctrl.com/static/help/en/api/index.html#/account>\
Fetched: 2026-10-23 (UTC)

## Account

The following API endpoints are for managing accounts. To avoid confusion: We are talking about financial accounts (assets, liabilities, etc.), i.e. the chart of accounts, not user accounts and not bank accounts.

### Read account

Returns a single account by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/account/read.json
```

### List accounts

Returns a list of all accounts.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/category">Account category</a>.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active accounts. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/list.json
```

### Export to Excel

Returns an Excel file of the account list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/category">Account category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active accounts. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/list.xlsx
```

### Export to CSV

Returns a CSV file of the account list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/category">Account category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active accounts. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/list.csv
```

### Export to PDF

Returns a PDF file of the account list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/category">Account category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active accounts. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/list.pdf
```

### Get account balance

Returns the balance of a single account for the given date.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the account. |
| `date` | optional, DATE | The date for the balance (always end of day). Defaults to the last day of the current fiscal period. See [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json).<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/account/balance
```

### Create account

Creates a new account. The account number must be unique. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>mandatory, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/category">Account category</a>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the account.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>number</code></th><td>mandatory, NUMBER, MAX:20</td><td>The account number. Must be numeric but can contain a decimal point.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers, if this account is either an expense or revenue account.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the account's currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark this account as inactive. Inactive accounts are greyed out in the list and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>targetMax</code></th><td>optional, NUMBER</td><td>The target maximum balance (aka budget) you hope this account to stay beneath of by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
<tr><th><code>targetMin</code></th><td>optional, NUMBER</td><td>The target minimum balance you hope this account to hit by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code associated with this account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/account/create.json
```

### Update account

Updates an existing account. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>mandatory, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/category">Account category</a>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the account to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the account.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>number</code></th><td>mandatory, NUMBER, MAX:20</td><td>The account number. Must be numeric but can contain a decimal point.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers, if this account is either an expense or revenue account.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the account's currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark this account as inactive. Inactive accounts are greyed out in the list and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>targetMax</code></th><td>optional, NUMBER</td><td>The target maximum balance (aka budget) you hope this account to stay beneath of by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
<tr><th><code>targetMin</code></th><td>optional, NUMBER</td><td>The target minimum balance you hope this account to hit by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code associated with this account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/account/update.json
```

### Delete accounts

Deletes one or multiple accounts. Only unused accounts can be deleted (accounts without any journal entries). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/account/delete.json
```

### Categorize accounts

Assigns one or multiple accounts to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/account/categorize.json
```

### Update attachments

Updates the file attachments of an account. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/account/update_attachments.json
```

## Bank account

The following API endpoints are for managing bank accounts.

### Read bank account

Returns a single bank account by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/account/bank/read.json
```

### List bank accounts

Returns a list of all bank accounts.

#### Parameters

<table>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/bank/list.json
```

### Export to Excel

Returns an Excel file of the bank account list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/bank/list.xlsx
```

### Export to CSV

Returns a CSV file of the bank account list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/bank/list.csv
```

### Export to PDF

Returns a PDF file of the bank account list.

#### Parameters

<table>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'name'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/bank/list.pdf
```

### Create bank account

Creates a new bank account. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>bic</code></th><td>mandatory, TEXT, MAX:11</td><td>The BIC (Business Identifier Code) of your bank.</td></tr>
<tr><th><code>iban</code></th><td>mandatory, TEXT, MAX:32</td><td>The IBAN (International Bank Account Number).</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the bank account.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of bank account, i.e. what is the bank account used for? Possible values: DEFAULT, ORDER, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>The ID of the financial account linked to this bank account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark this bank account as inactive. Inactive bank accounts are greyed out in the list and are no longer suggested by the app. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>qrFirstDigits</code></th><td>optional, NUMBER, MAX:8</td><td>The first few digits of the Swiss QR reference (0 by default). This is specific to Switzerland.</td></tr>
<tr><th><code>qrIban</code></th><td>optional, TEXT, MAX:32</td><td>The QR-IBAN, which is an IBAN especially for QR invoices (former ESR). This is specific to Switzerland.</td></tr>
<tr><th><code>url</code></th><td>optional, TEXT, MAX:255</td><td>An optional URL for the bank's e-banking portal.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/account/bank/create.json
```

### Update bank account

Updates an existing bank account. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>bic</code></th><td>mandatory, TEXT, MAX:11</td><td>The BIC (Business Identifier Code) of your bank.</td></tr>
<tr><th><code>iban</code></th><td>mandatory, TEXT, MAX:32</td><td>The IBAN (International Bank Account Number).</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the bank account to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the bank account.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of bank account, i.e. what is the bank account used for? Possible values: DEFAULT, ORDER, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>The ID of the financial account linked to this bank account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark this bank account as inactive. Inactive bank accounts are greyed out in the list and are no longer suggested by the app. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>qrFirstDigits</code></th><td>optional, NUMBER, MAX:8</td><td>The first few digits of the Swiss QR reference (0 by default). This is specific to Switzerland.</td></tr>
<tr><th><code>qrIban</code></th><td>optional, TEXT, MAX:32</td><td>The QR-IBAN, which is an IBAN especially for QR invoices (former ESR). This is specific to Switzerland.</td></tr>
<tr><th><code>url</code></th><td>optional, TEXT, MAX:255</td><td>An optional URL for the bank's e-banking portal.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/account/bank/update.json
```

### Delete bank accounts

Deletes one or multiple bank accounts. Only unused bank accounts can be deleted (which are not referenced anywhere). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/account/bank/delete.json
```

### Update attachments

Updates the file attachments of a bank account. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/account/bank/update_attachments.json
```

## Category

The following API endpoints are for managing account categories. Note that the top categories (assets, liabilities, etc.) cannot be manipulated.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/account/category/read.json
```

### List categories

Returns a list of all categories.

#### Endpoint

```
GET /api/v1/account/category/list.json
```

### Get tree of categories

Returns a tree of all categories or the tree below a parent category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | Optional ID of the parent category (omit to get all categories). |

#### Endpoint

```
GET /api/v1/account/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:100 | The name of the account category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `number` | optional, TEXT, MAX:20 | The number of the account category according to the chart of accounts. Must be numeric. This is used for sorting the categories. |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/account/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the category to update. |
| `name` | mandatory, TEXT, MAX:100 | The name of the account category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `number` | optional, TEXT, MAX:20 | The number of the account category according to the chart of accounts. Must be numeric. This is used for sorting the categories. |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/account/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/account/category/delete.json
```

## Cost center

The following API endpoints are for managing cost centers.

### Read cost center

Returns a single cost center by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/account/costcenter/read.json
```

### List cost centers

Returns a list of all cost centers.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter/category">Cost center category</a>.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/costcenter/list.json
```

### Export to Excel

Returns an Excel file of the cost center list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter/category">Cost center category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/costcenter/list.xlsx
```

### Export to CSV

Returns a CSV file of the cost center list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter/category">Cost center category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/costcenter/list.csv
```

### Export to PDF

Returns a PDF file of the cost center list.

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter the list by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter/category">Cost center category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'ASC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the balances.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to only include active cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'number'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/account/costcenter/list.pdf
```

### Get cost center balance

Returns the balance of a single cost center for the given date.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the cost center. |
| `date` | optional, DATE | The date for the balance (always end of day). Defaults to the last day of the current fiscal period. See [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json).<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/account/costcenter/balance
```

### Create cost center

Creates a new cost center. The cost center number must be unique. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the cost center.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>number</code></th><td>mandatory, NUMBER, MAX:20</td><td>The cost center number. Must be numeric but can contain a decimal point.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter/category">Cost center category</a>.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark this cost center as inactive. Inactive cost centers are greyed out in the list and are no longer suggested by the app. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>targetMax</code></th><td>optional, NUMBER</td><td>The target maximum balance (aka budget) you hope this cost center to stay beneath of by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
<tr><th><code>targetMin</code></th><td>optional, NUMBER</td><td>The target minimum balance you hope this cost center / cost unit to hit by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/account/costcenter/create.json
```

### Update cost center

Updates an existing cost center. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the cost center to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the cost center.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>number</code></th><td>mandatory, NUMBER, MAX:20</td><td>The cost center number. Must be numeric but can contain a decimal point.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter/category">Cost center category</a>.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark this cost center as inactive. Inactive cost centers are greyed out in the list and are no longer suggested by the app. Possible values: true, false.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>targetMax</code></th><td>optional, NUMBER</td><td>The target maximum balance (aka budget) you hope this cost center to stay beneath of by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
<tr><th><code>targetMin</code></th><td>optional, NUMBER</td><td>The target minimum balance you hope this cost center / cost unit to hit by the end of the fiscal period. This will then be displayed by the Targets report, comparing your target to the actual balance. Please first switch to the desired fiscal period to set the target for that period, see <a href="https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json">Switch fiscal period</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/account/costcenter/update.json
```

### Delete cost centers

Deletes one or multiple cost centers. Only unused cost centers can be deleted (cost centers without any journal entries). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/account/costcenter/delete.json
```

### Categorize cost centers

Assigns one or multiple cost centers to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/account/costcenter/categorize.json
```

### Update attachments

Updates the file attachments of a cost center. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/account/costcenter/update_attachments.json
```

## Cost center category

The following API endpoints are for managing cost center categories.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/account/costcenter/category/read.json
```

### List categories

Returns a list of all categories.

#### Endpoint

```
GET /api/v1/account/costcenter/category/list.json
```

### Get tree of categories

Returns a tree of all categories or the tree below a parent category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | Optional ID of the parent category (omit to get all categories). |

#### Endpoint

```
GET /api/v1/account/costcenter/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:100 | The name of the cost center category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `number` | optional, TEXT, MAX:20 | An optional number for the cost center category. Must be numeric. This is used for sorting the categories. |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/account/costcenter/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the category to update. |
| `name` | mandatory, TEXT, MAX:100 | The name of the cost center category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `number` | optional, TEXT, MAX:20 | An optional number for the cost center category. Must be numeric. This is used for sorting the categories. |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/account/costcenter/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/account/costcenter/category/delete.json
```
