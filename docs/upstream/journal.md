Source: <https://app.cashctrl.com/static/help/en/api/index.html#/journal>

## Journal

The following API endpoints are for managing journal entries. Any kind of entry can be read but only manual book entries can be manipulated. Automatic book entries happen for example through orders, depreciations or currency exchange rate corrections. They cannot be manipulated here but in the respective API (e.g. [Orders](https://app.cashctrl.com/static/help/en/api/index.html#/order)).

### Read journal entry

Returns a single journal entry by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/journal/read.json
```

### List journal entries

Returns a list of journal entries.

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>Optional ID of account to retrieve the journal for that specific account.</td></tr>
<tr><th><code>associateId</code></th><td>optional, NUMBER</td><td>Optional ID of an associate to retrieve the journal for that specific person.</td></tr>
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
<tr><th><code>onlyCollective</code></th><td>optional, BOOLEAN</td><td>Flag to only include collective book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyImported</code></th><td>optional, BOOLEAN</td><td>Flag to only include imported book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyManual</code></th><td>optional, BOOLEAN</td><td>Flag to only include manual book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyPurchase</code></th><td>optional, BOOLEAN</td><td>Flag to only include purchase order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySalary</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySales</code></th><td>optional, BOOLEAN</td><td>Flag to only include sales order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyUntaxed</code></th><td>optional, BOOLEAN</td><td>Flag to only include untaxed book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/list.json
```

### Export to Excel

Returns an Excel file of the entries list.

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>Optional ID of account to retrieve the journal for that specific account.</td></tr>
<tr><th><code>associateId</code></th><td>optional, NUMBER</td><td>Optional ID of an associate to retrieve the journal for that specific person.</td></tr>
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
<tr><th><code>onlyCollective</code></th><td>optional, BOOLEAN</td><td>Flag to only include collective book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyImported</code></th><td>optional, BOOLEAN</td><td>Flag to only include imported book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyManual</code></th><td>optional, BOOLEAN</td><td>Flag to only include manual book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyPurchase</code></th><td>optional, BOOLEAN</td><td>Flag to only include purchase order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySalary</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySales</code></th><td>optional, BOOLEAN</td><td>Flag to only include sales order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyUntaxed</code></th><td>optional, BOOLEAN</td><td>Flag to only include untaxed book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/list.xlsx
```

### Export to CSV

Returns a CSV file of the entries list.

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>Optional ID of account to retrieve the journal for that specific account.</td></tr>
<tr><th><code>associateId</code></th><td>optional, NUMBER</td><td>Optional ID of an associate to retrieve the journal for that specific person.</td></tr>
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
<tr><th><code>onlyCollective</code></th><td>optional, BOOLEAN</td><td>Flag to only include collective book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyImported</code></th><td>optional, BOOLEAN</td><td>Flag to only include imported book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyManual</code></th><td>optional, BOOLEAN</td><td>Flag to only include manual book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyPurchase</code></th><td>optional, BOOLEAN</td><td>Flag to only include purchase order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySalary</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySales</code></th><td>optional, BOOLEAN</td><td>Flag to only include sales order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyUntaxed</code></th><td>optional, BOOLEAN</td><td>Flag to only include untaxed book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/list.csv
```

### Export to PDF

Returns a PDF file of the entries list.

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>Optional ID of account to retrieve the journal for that specific account.</td></tr>
<tr><th><code>associateId</code></th><td>optional, NUMBER</td><td>Optional ID of an associate to retrieve the journal for that specific person.</td></tr>
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
<tr><th><code>onlyCollective</code></th><td>optional, BOOLEAN</td><td>Flag to only include collective book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyImported</code></th><td>optional, BOOLEAN</td><td>Flag to only include imported book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyManual</code></th><td>optional, BOOLEAN</td><td>Flag to only include manual book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyPurchase</code></th><td>optional, BOOLEAN</td><td>Flag to only include purchase order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySalary</code></th><td>optional, BOOLEAN</td><td>Flag to only include salary book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlySales</code></th><td>optional, BOOLEAN</td><td>Flag to only include sales order book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyUntaxed</code></th><td>optional, BOOLEAN</td><td>Flag to only include untaxed book entries. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/list.pdf
```

### Create journal entry

Creates a new manual journal entry. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>amount</code></th><td>mandatory, NUMBER</td><td>The amount of the book entry (e.g. 125.50). This parameter is ignored if <code>items</code> is set.</td></tr>
<tr><th><code>creditId</code></th><td>mandatory, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>. This parameter is ignored if <code>items</code> is set.</td></tr>
<tr><th><code>debitId</code></th><td>mandatory, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>. This parameter is ignored if <code>items</code> is set.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>associateId</code></th><td>optional, TEXT</td><td>The ID of the business associate (person). Instead of an ID you can also create a new person on-the-fly by entering a name here. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>dateAdded</code></th><td>optional, DATE</td><td>The date of the book entry.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next book entry will be created X days before the start date. Leave empty or set to 0 to have the next book entry created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence. Orders repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>items</code></th><td>optional, JSON</td><td>Items for the collective book entry (Sammelbuchung). Omit to create a regular book entry, and set if you want to create a collective book entry.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>associateId</code></th><td>optional, TEXT</td><td>The ID of the business associate (person). Instead of an ID you can also create a new person on-the-fly by entering a name here. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>credit</code></th><td>optional, NUMBER</td><td>The amount on the credit side. Either <code>debit</code> or <code>credit</code> must be set.</td></tr>
<tr><th><code>debit</code></th><td>optional, NUMBER</td><td>The amount on the debit side. Either <code>debit</code> or <code>credit</code> must be set.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>The description of the item.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether or not to send a notification e-mail when book entries have been created. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the book entry should be automatically repeated. Leave empty to not repeat the book entry (or to remove recurrence). Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>reference</code></th><td>optional, TEXT, MAX:100</td><td>An optional reference / receipt for the book entry. Can be automatically generated using <code>sequenceNumberId</code>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the reference (see <code>reference</code>). If this is empty, the sequence number will not update when <code>reference</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence. This is the date when the book entry will be repeated next.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>title</code></th><td>optional, TEXT, MAX:250</td><td>The description of the book entry.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/journal/create.json
```

### Update journal entry

Updates an existing manual journal entry. Note that you cannot update automatically created entries this way (use the appropriate API, e.g. [Orders](https://app.cashctrl.com/static/help/en/api/index.html#/order)). Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>amount</code></th><td>mandatory, NUMBER</td><td>The amount of the book entry (e.g. 125.50). This parameter is ignored if <code>items</code> is set.</td></tr>
<tr><th><code>creditId</code></th><td>mandatory, NUMBER</td><td>The ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>. This parameter is ignored if <code>items</code> is set.</td></tr>
<tr><th><code>debitId</code></th><td>mandatory, NUMBER</td><td>The ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>. This parameter is ignored if <code>items</code> is set.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the journal entry to update.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>associateId</code></th><td>optional, TEXT</td><td>The ID of the business associate (person). Instead of an ID you can also create a new person on-the-fly by entering a name here. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>dateAdded</code></th><td>optional, DATE</td><td>The date of the book entry.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next book entry will be created X days before the start date. Leave empty or set to 0 to have the next book entry created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence. Orders repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>items</code></th><td>optional, JSON</td><td>Items for the collective book entry (Sammelbuchung). Omit to create a regular book entry, and set if you want to create a collective book entry.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>associateId</code></th><td>optional, TEXT</td><td>The ID of the business associate (person). Instead of an ID you can also create a new person on-the-fly by entering a name here. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>credit</code></th><td>optional, NUMBER</td><td>The amount on the credit side. Either <code>debit</code> or <code>credit</code> must be set.</td></tr>
<tr><th><code>debit</code></th><td>optional, NUMBER</td><td>The amount on the debit side. Either <code>debit</code> or <code>credit</code> must be set.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>The description of the item.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether or not to send a notification e-mail when book entries have been created. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the book entry should be automatically repeated. Leave empty to not repeat the book entry (or to remove recurrence). Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>reference</code></th><td>optional, TEXT, MAX:100</td><td>An optional reference / receipt for the book entry. Can be automatically generated using <code>sequenceNumberId</code>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the reference (see <code>reference</code>). If this is empty, the sequence number will not update when <code>reference</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence. This is the date when the book entry will be repeated next.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>title</code></th><td>optional, TEXT, MAX:250</td><td>The description of the book entry.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/journal/update.json
```

### Delete journal entries

Deletes one or multiple manual journal entries. Note that you cannot delete automatically created entries here (use the appropriate API, e.g. [Orders](https://app.cashctrl.com/static/help/en/api/index.html#/order)). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/journal/delete.json
```

### Update attachments

Updates the file attachments of a journal entry. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/journal/update_attachments.json
```

### Update recurrence

Updates the recurrence of an existing book entry by journal ID. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the journal book entry. |
| `daysBefore` | optional, NUMBER | The next book entry will be created X days before the start date. Leave empty or set to 0 to have the next book entry created on the start date itself. See `recurrence` parameter. |
| `endDate` | optional, DATE | The end date for the recurrence. Orders repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `notifyEmail` | optional, TEXT | The e-mail address to send a notification to. See `notifyType` parameter. |
| `notifyPersonId` | optional, NUMBER | The ID of the person to send a notification to. See `notifyType` parameter. |
| `notifyType` | optional, TEXT | Whether or not to send a notification e-mail when book entries have been created. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL. |
| `notifyUserId` | optional, NUMBER | The ID of the user to send a notification to. See `notifyType` parameter. Note: User must be in this organization. |
| `recurrence` | optional, TEXT | The interval of how often the book entry should be automatically repeated. Leave empty to not repeat the book entry (or to remove recurrence). Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY. |
| `startDate` | optional, DATE | The start date for the recurrence. This is the date when the book entry will be repeated next.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
POST /api/v1/journal/update_recurrence.json
```

## Import

The following API endpoints are for managing imports of journal entries via MT940 or ISO 20022 camt files. An import object contains the raw file contents, and meta data like file name, content type, etc. For the actual entries, see [Journal import entry](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import/entry).

### Read import

Returns a single import object by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/journal/import/read.json
```

### List imports

Returns a list of imports.

#### Parameters

| | | |
| --- | --- | --- |
| `dir` | optional, TEXT | The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC. |
| `fiscalPeriodId` | optional, NUMBER | The ID of the fiscal period, from which we retrieve the imports. |
| `query` | optional, TEXT | Fulltext search query. |
| `sort` | optional, TEXT | The column to sort the list by. Defaults to 'created'. |

#### Endpoint

```
GET /api/v1/journal/import/list.json
```

### Create import

Creates a new import. This will persist the entries to be imported in the database (see [Journal import entry](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import/entry)), but doesn't actually import anything into the journal, yet. The entries have to be confirmed first, and then imported via the Execute endpoint (see next endpoint). Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>mappings</code></th><td>mandatory, JSON</td><td>Mappings from columns (Excel/CSV) or fixed values to fields in CashCtrl. Make sure that you set either the fixed value or the column value for the respective field. e.g. columnAmount or fixedAmount<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>columnAmount</code></th><td>optional, TEXT</td><td>The name of the amount column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnAssociateName</code></th><td>optional, TEXT</td><td>The name of the associate column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnCreditName</code></th><td>optional, TEXT</td><td>The name of the credit column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnCurrencyCode</code></th><td>optional, TEXT</td><td>The name of the currency column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnCurrencyRate</code></th><td>optional, TEXT</td><td>The name of the currency rate column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnDate</code></th><td>optional, TEXT</td><td>The name of the date column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnDebitName</code></th><td>optional, TEXT</td><td>The name of the debit column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnDescription</code></th><td>optional, TEXT</td><td>The name of the description column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnNotes</code></th><td>optional, TEXT</td><td>The name of the notes column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnReferenceReceipt</code></th><td>optional, TEXT</td><td>The name of the reference receipt column in the (Excel/CSV) file.</td></tr>
<tr><th><code>columnTaxRate</code></th><td>optional, TEXT</td><td>The name of the tax rate column in the (Excel/CSV) file.</td></tr>
<tr><th><code>conditions</code></th><td>optional, JSON</td><td>Book entry import conditions.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>compareMethod</code></th><td>mandatory, TEXT</td><td>The type of comparison between mappingColumn value and compareValue. Possible values: EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, GREATER_THAN, LESS_THAN, GREATER_OR_EQUALS, LESS_OR_EQUALS.</td></tr>
<tr><th><code>compareValue</code></th><td>mandatory, TEXT</td><td>The value with which the mappingColumn value is compared.</td></tr>
<tr><th><code>mappingColumn</code></th><td>mandatory, TEXT</td><td>The name of the column in the (Excel/CSV) file.</td></tr>
</table>
</td></tr>
<tr><th><code>customfields</code></th><td>optional, JSON</td><td>Book entry customfield mappings.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>customFieldId</code></th><td>mandatory, TEXT</td><td>The ID of the customfield to which the specified column or fixed value should be assigned.</td></tr>
<tr><th><code>fixedValue</code></th><td>optional, TEXT</td><td>The fixed value</td></tr>
<tr><th><code>mappingColumn</code></th><td>optional, TEXT</td><td>The name of the column in the (Excel/CSV) file.</td></tr>
</table>
</td></tr>
<tr><th><code>fixedAmount</code></th><td>optional, NUMBER</td><td>The fixed amount of the book entry (e.g. 125.50).</td></tr>
<tr><th><code>fixedAssociateId</code></th><td>optional, TEXT</td><td>The fixed ID of the business associate (person). Instead of an ID you can also create a new person on-the-fly by entering a name here. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>fixedCreditId</code></th><td>optional, NUMBER</td><td>The fixed ID of the account on the credit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>fixedCurrencyCodeId</code></th><td>optional, NUMBER</td><td>The fixed ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>fixedCurrencyRate</code></th><td>optional, NUMBER</td><td>The fixed exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>fixedDate</code></th><td>optional, DATE</td><td>The fixed date of the book entry.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>fixedDebitId</code></th><td>optional, NUMBER</td><td>The fixed ID of the account on the debit side. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>fixedDescription</code></th><td>optional, TEXT, MAX:250</td><td>The fixed description of the book entry.</td></tr>
<tr><th><code>fixedNotes</code></th><td>optional, TEXT</td><td>The fixed notes of the book entry.</td></tr>
<tr><th><code>fixedReferenceReceipt</code></th><td>optional, TEXT, MAX:100</td><td>A fixed optional reference / receipt for the book entry.</td></tr>
<tr><th><code>fixedTaxRateId</code></th><td>optional, NUMBER</td><td>The fixed ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>File to import. Valid formats: camt.052, camt.053, camt.054, MT940, Excel, CSV and any of these formats within a ZIP or TAR file. Max. size: 5 MB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>isForceSequenceNumber</code></th><td>optional, BOOLEAN</td><td>Force the use of sequence numbers? Otherwise imports the reference number if exists. Defaults to false Possible values: true, false.</td></tr>
<tr><th><code>skipRows</code></th><td>optional, NUMBER</td><td>The number of lines that are skipped before the file is parsed. Useful if the header line is not the first line in the file.</td></tr>
<tr><th><code>targetAccountId</code></th><td>optional, NUMBER</td><td>The ID of the target account (e.g. your bank account) to import the entries into.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/journal/import/create.json
```

### Execute import

Executes a import. This means that all confirmed entries are actually imported into the journal. To confirm entries, see [Journal import entry](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import/entry). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
POST /api/v1/journal/import/execute.json
```

## Import entry

The following API endpoints are for managing journal import entries. These entries have been created by a [Journal import](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import) and are to be imported into the journal. They are not yet imported unless the entries have been confirmed (see [Confirm import entry](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import/entry/confirm.json)) and the import has been executed (see [Execute journal import](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import/execute.json)).

### Read import entry

Returns a single import entry by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/journal/import/entry/read.json
```

### List import entries

Returns a list of import entries.

#### Parameters

<table>
<tr><th><code>importId</code></th><td>mandatory, NUMBER</td><td>The ID of the journal import.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/import/entry/list.json
```

### Export to Excel

Returns an Excel file of the entries list.

#### Parameters

<table>
<tr><th><code>importId</code></th><td>mandatory, NUMBER</td><td>The ID of the journal import.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/import/entry/list.xlsx
```

### Export to CSV

Returns a CSV file of the entries list.

#### Parameters

<table>
<tr><th><code>importId</code></th><td>mandatory, NUMBER</td><td>The ID of the journal import.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/import/entry/list.csv
```

### Export to PDF

Returns a PDF file of the entries list.

#### Parameters

<table>
<tr><th><code>importId</code></th><td>mandatory, NUMBER</td><td>The ID of the journal import.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/journal/import/entry/list.pdf
```

### Update import entry

Updates an import entry. Note that this automatically confirms the entry. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>amount</code></th><td>mandatory, NUMBER</td><td>The amount of the journal entry (e.g. 125.50).</td></tr>
<tr><th><code>contraAccountId</code></th><td>mandatory, NUMBER</td><td>The ID of the contra account. That's the account opposite of the target account that we import into. For example if the target account is a bank account, the contra account may be an expense or revenue account. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateAdded</code></th><td>mandatory, DATE</td><td>The date of the book entry.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the import entry to update.</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>associateId</code></th><td>optional, TEXT</td><td>The ID of the business associate (person). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>orderId</code></th><td>optional, NUMBER</td><td>The ID of the order that this book entry belongs to. This is the case, for example, if this book entry is a payment for an existing order.</td></tr>
<tr><th><code>reference</code></th><td>optional, TEXT, MAX:100</td><td>An optional reference / receipt for the book entry.</td></tr>
<tr><th><code>statementId</code></th><td>optional, NUMBER</td><td>The ID of the salary statement that this book entry belongs to. This is the case, for example, if this book entry is a payment for an existing salary statement.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of either the order status or salary statement status, depending on whether <code>orderId</code> or <code>statementId</code> is set. This updates the status of the document, e.g. from 'Open' to 'Paid'.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>title</code></th><td>optional, TEXT, MAX:250</td><td>The description of the book entry.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/journal/import/entry/update.json
```

### Ignore import entries

Ignores one or multiple import entries. This doesn't actually delete the entry but marks it as ignored, which is to say: Do not import. You can restore ignored entries, see next API endpoint. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/journal/import/entry/delete.json
```

### Restore import entries

Restores one or multiple import entries. This restores ignored import entries. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/journal/import/entry/restore.json
```

### Confirm import entries

Confirms one or multiple import entries. Confirmed entries are ready to be imported with [Execute journal import](https://app.cashctrl.com/static/help/en/api/index.html#/journal/import/execute.json). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/journal/import/entry/confirm.json
```

### Unconfirm import entries

Unconfirms one or multiple import entries. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/journal/import/entry/unconfirm.json
```
