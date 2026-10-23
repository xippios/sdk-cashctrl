Source: <https://app.cashctrl.com/static/help/en/api/index.html#/order>

## Order

The following API endpoints are for managing order objects like offers, invoices, delivery notes, etc., both sales and purchase orders.

### Read order

Returns a single order by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/read.json
```

### List orders

Returns a list of orders per type (sales or purchase).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the order category to filter by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the orders.</td></tr>
<tr><th><code>groupId</code></th><td>optional, NUMBER</td><td>The ID of the order group (dossier) to filter by.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open orders (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include orders that are overdue (past the due date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>The ID of a person to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of the order status to filter by.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of order (sales or purchase). Possible values: SALES, PURCHASE.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/order/list.json
```

### Export to Excel

Returns an Excel file of the orders list per type (sales or purchase).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the order category to filter by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the orders.</td></tr>
<tr><th><code>groupId</code></th><td>optional, NUMBER</td><td>The ID of the order group (dossier) to filter by.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open orders (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include orders that are overdue (past the due date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>The ID of a person to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of the order status to filter by.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of order (sales or purchase). Possible values: SALES, PURCHASE.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/order/list.xlsx
```

### Export to CSV

Returns a CSV file of the orders list per type (sales or purchase).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the order category to filter by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the orders.</td></tr>
<tr><th><code>groupId</code></th><td>optional, NUMBER</td><td>The ID of the order group (dossier) to filter by.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open orders (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include orders that are overdue (past the due date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>The ID of a person to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of the order status to filter by.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of order (sales or purchase). Possible values: SALES, PURCHASE.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/order/list.csv
```

### Export to PDF

Returns a PDF file of the orders list per type (sales or purchase).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the order category to filter by. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the orders.</td></tr>
<tr><th><code>groupId</code></th><td>optional, NUMBER</td><td>The ID of the order group (dossier) to filter by.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOpen</code></th><td>optional, BOOLEAN</td><td>Flag to only include open orders (incomplete status like 'Open' as opposed to completed status like 'Paid'). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyOverdue</code></th><td>optional, BOOLEAN</td><td>Flag to only include orders that are overdue (past the due date). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>The ID of a person to filter by.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'date'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of the order status to filter by.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of order (sales or purchase). Possible values: SALES, PURCHASE.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/order/list.pdf
```

### Create order

Creates a new order. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>associateId</code></th><td>mandatory, CSV</td><td>The IDs of one or multiple business partners (customers / vendors), comma-separated. If you enter multiple IDs it will create a separate document for each business partner. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>categoryId</code></th><td>mandatory, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
<tr><th><code>date</code></th><td>mandatory, DATE</td><td>The date of the order.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>The ID of the account. Leave empty to use the account from the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next order will be created X days before the start date. Leave empty or set to 0 to have the next order created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:200</td><td>A description of the order document.</td></tr>
<tr><th><code>discountPercentage</code></th><td>optional, NUMBER, MIN:0.0, MAX:100.0</td><td>The discount percentage for the entire order (can be overriden in items).</td></tr>
<tr><th><code>dueDays</code></th><td>optional, NUMBER</td><td>The due days. Order date + due days = Due date (the date, when payment is due).</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence (see <code>recurrence</code> parameter). Orders repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>groupId</code></th><td>optional, NUMBER</td><td>The ID of the order group (dossier). Use this to include the order in a dossier with other orders that belong together (e.g. the offer, order confirmation, delivery note and invoice of the same order). This is overridden by <code>previousId</code> (if both are set).</td></tr>
<tr><th><code>isDisplayItemGross</code></th><td>optional, BOOLEAN</td><td>Whether to display item totals as gross (including tax). Defaults to false (net). Possible values: true, false.</td></tr>
<tr><th><code>items</code></th><td>optional, JSON</td><td>The list of order items.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account (revenue account for sales, expense account for purchase). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>The name of the item.</td></tr>
<tr><th><code>unitPrice</code></th><td>mandatory, NUMBER</td><td>The price of the item (for one unit).</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>articleNr</code></th><td>optional, TEXT</td><td>The article number.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>A description of the item.</td></tr>
<tr><th><code>discountPercentage</code></th><td>optional, NUMBER</td><td>Discount percentage for the item price.</td></tr>
<tr><th><code>inventoryId</code></th><td>optional, NUMBER</td><td>The ID of the inventory article. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory">Inventory</a>.</td></tr>
<tr><th><code>quantity</code></th><td>optional, NUMBER</td><td>The amount of units of the item. Defaults to 1.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of item. Defaults to ARTICLE. Possible values: ARTICLE, TEXT, PAGEBREAK, SUBTOTAL, TITLE, OPTIONTOTAL.</td></tr>
<tr><th><code>unitId</code></th><td>optional, TEXT</td><td>The ID of the unit (pcs., hours, etc.). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/unit">Units</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>language</code></th><td>optional, TEXT</td><td>The language of the document. Possible values: DE, EN, FR, IT.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether to send a notification e-mail when orders have been created or not. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The order number (e.g. 'IN-2001015' for an invoice). Leave empty to generate the number with <code>sequenceNumberId</code>. This becomes mandatory if a sequence number is set neither here nor in the order category.</td></tr>
<tr><th><code>previousId</code></th><td>optional, NUMBER</td><td>The ID of the previous order from which this order is created (Next step / Continue as). The new order will be grouped with the previous order in a dossier. See also <code>groupId</code>. This will override <code>groupId</code> (if both are set).</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the order should be automatically repeated. Leave empty to not repeat the order. See also <code>startDate</code> and <code>endDate</code>. Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>responsiblePersonId</code></th><td>optional, TEXT</td><td>The ID of the responsible person (Sachbearbeiter). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>roundingId</code></th><td>optional, NUMBER</td><td>The ID of the rounding to use for the grand total. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/rounding">Rounding</a>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the order number (see <code>nr</code>). If empty, the sequence number of the category is used (if set). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence (see <code>recurrence</code> parameter). This is the date when the order will be repeated next. Should probably be called <code>nextDate</code> instead.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of the status to set. Leave empty to use the first status in the list. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/order/create.json
```

### Update order

Updates an existing order. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>associateId</code></th><td>mandatory, NUMBER</td><td>The ID of the business partner (customer / vendor). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>categoryId</code></th><td>mandatory, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
<tr><th><code>date</code></th><td>mandatory, DATE</td><td>The date of the order.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the order to update.</td></tr>
<tr><th><code>accountId</code></th><td>optional, NUMBER</td><td>The ID of the account. Leave empty to use the account from the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>currencyRate</code></th><td>optional, NUMBER</td><td>The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>daysBefore</code></th><td>optional, NUMBER</td><td>The next order will be created X days before the start date. Leave empty or set to 0 to have the next order created on the start date itself. See <code>recurrence</code> parameter.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:200</td><td>A description of the order document.</td></tr>
<tr><th><code>discountPercentage</code></th><td>optional, NUMBER, MIN:0.0, MAX:100.0</td><td>The discount percentage for the entire order (can be overriden in items).</td></tr>
<tr><th><code>dueDays</code></th><td>optional, NUMBER</td><td>The due days. Order date + due days = Due date (the date, when payment is due).</td></tr>
<tr><th><code>endDate</code></th><td>optional, DATE</td><td>The end date for the recurrence (see <code>recurrence</code> parameter). Orders repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>groupId</code></th><td>optional, NUMBER</td><td>The ID of the order group (dossier). Use this to include the order in a dossier with other orders that belong together (e.g. the offer, order confirmation, delivery note and invoice of the same order). This is overridden by <code>previousId</code> (if both are set).</td></tr>
<tr><th><code>isDisplayItemGross</code></th><td>optional, BOOLEAN</td><td>Whether to display item totals as gross (including tax). Defaults to false (net). Possible values: true, false.</td></tr>
<tr><th><code>items</code></th><td>optional, JSON</td><td>The list of order items.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account (revenue account for sales, expense account for purchase). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>The name of the item.</td></tr>
<tr><th><code>unitPrice</code></th><td>mandatory, NUMBER</td><td>The price of the item (for one unit).</td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>articleNr</code></th><td>optional, TEXT</td><td>The article number.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>A description of the item.</td></tr>
<tr><th><code>discountPercentage</code></th><td>optional, NUMBER</td><td>Discount percentage for the item price.</td></tr>
<tr><th><code>inventoryId</code></th><td>optional, NUMBER</td><td>The ID of the inventory article. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory">Inventory</a>.</td></tr>
<tr><th><code>quantity</code></th><td>optional, NUMBER</td><td>The amount of units of the item. Defaults to 1.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of item. Defaults to ARTICLE. Possible values: ARTICLE, TEXT, PAGEBREAK, SUBTOTAL, TITLE, OPTIONTOTAL.</td></tr>
<tr><th><code>unitId</code></th><td>optional, TEXT</td><td>The ID of the unit (pcs., hours, etc.). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/unit">Units</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>language</code></th><td>optional, TEXT</td><td>The language of the document. Possible values: DE, EN, FR, IT.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>notifyEmail</code></th><td>optional, TEXT</td><td>The e-mail address to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyPersonId</code></th><td>optional, NUMBER</td><td>The ID of the person to send a notification to. See <code>notifyType</code> parameter.</td></tr>
<tr><th><code>notifyType</code></th><td>optional, TEXT</td><td>Whether to send a notification e-mail when orders have been created or not. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL.</td></tr>
<tr><th><code>notifyUserId</code></th><td>optional, NUMBER</td><td>The ID of the user to send a notification to. See <code>notifyType</code> parameter. Note: User must be in this organization.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The order number (e.g. 'IN-2001015' for an invoice). Leave empty to generate the number with <code>sequenceNumberId</code>. This becomes mandatory if a sequence number is set neither here nor in the order category.</td></tr>
<tr><th><code>previousId</code></th><td>optional, NUMBER</td><td>The ID of the previous order from which this order is created (Next step / Continue as). The new order will be grouped with the previous order in a dossier. See also <code>groupId</code>. This will override <code>groupId</code> (if both are set).</td></tr>
<tr><th><code>recurrence</code></th><td>optional, TEXT</td><td>The interval of how often the order should be automatically repeated. Leave empty to not repeat the order. See also <code>startDate</code> and <code>endDate</code>. Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY.</td></tr>
<tr><th><code>responsiblePersonId</code></th><td>optional, TEXT</td><td>The ID of the responsible person (Sachbearbeiter). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>roundingId</code></th><td>optional, NUMBER</td><td>The ID of the rounding to use for the grand total. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/rounding">Rounding</a>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the order number (see <code>nr</code>). If empty, the sequence number of the category is used (if set). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>startDate</code></th><td>optional, DATE</td><td>The start date for the recurrence (see <code>recurrence</code> parameter). This is the date when the order will be repeated next. Should probably be called <code>nextDate</code> instead.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>statusId</code></th><td>optional, NUMBER</td><td>The ID of the status to set. Leave empty to use the first status in the list. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/category">Order category</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/order/update.json
```

### Delete orders

Deletes one or multiple orders. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/order/delete.json
```

### Update status

Updates the status of an existing order by order ID. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple orders, comma-separated. |
| `statusId` | mandatory, NUMBER | The ID of the new status. |

#### Endpoint

```
POST /api/v1/order/update_status.json
```

### Update recurrence

Updates the recurrence of an existing order by order ID. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the order. |
| `daysBefore` | optional, NUMBER | The next order will be created X days before the start date. Leave empty or set to 0 to have the next order created on the start date itself. See `recurrence` parameter. |
| `endDate` | optional, DATE | The end date for the recurrence. Orders repeat automatically up until this date, when the recurrence will stop.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `notifyEmail` | optional, TEXT | The e-mail address to send a notification to. See `notifyType` parameter. |
| `notifyPersonId` | optional, NUMBER | The ID of the person to send a notification to. See `notifyType` parameter. |
| `notifyType` | optional, TEXT | Whether or not to send a notification e-mail when orders have been created. Leave empty to not send any notification. Possible values: NONE, USER, PERSON, RESPONSIBLE_PERSON, EMAIL. |
| `notifyUserId` | optional, NUMBER | The ID of the user to send a notification to. See `notifyType` parameter. Note: User must be in this organization. |
| `recurrence` | optional, TEXT | The interval of how often the order should be automatically repeated. Leave empty to not repeat the order (or to remove recurrence). Possible values: MONTHLY, WEEKLY, DAILY, YEARLY, SEMESTRAL, QUARTERLY, BI_MONTHLY, BI_WEEKLY. |
| `startDate` | optional, DATE | The start date for the recurrence. This is the date when the order will be repeated next.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
POST /api/v1/order/update_recurrence.json
```

### Continue as

Continue an order as another order (e.g. continue an offer as an invoice). Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `categoryId` | mandatory, NUMBER | The ID of the target category. |
| `ids` | mandatory, CSV | The IDs of one or multiple orders to continue, comma-separated. |
| `associateId` | optional, TEXT | The ID of the business partner (customer / vendor). Mandatory only if changing between sales and purchase order. See [Person](https://app.cashctrl.com/static/help/en/api/index.html#/person). |
| `date` | optional, DATE | The date of the order. Leave empty to use today.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `notes` | optional, HTML | Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `statusId` | optional, NUMBER | The ID of the status to set. Leave empty to use the first status in the list. See [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category). |

#### Endpoint

```
POST /api/v1/order/continue.json
```

### Read dossier

Reads a dossier (group of orders that belong together).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/dossier.json
```

### Add to dossier

Adds one or multiple orders to a dossier.

#### Parameters

| | | |
| --- | --- | --- |
| `groupId` | mandatory, NUMBER | The ID of the group. |
| `ids` | mandatory, CSV | The IDs of the orders to add/remove, comma-separated. |

#### Endpoint

```
POST /api/v1/order/dossier_add.json
```

### Remove from dossier

Removes one or multiple orders from a dossier.

#### Parameters

| | | |
| --- | --- | --- |
| `groupId` | mandatory, NUMBER | The ID of the group. |
| `ids` | mandatory, CSV | The IDs of the orders to add/remove, comma-separated. |

#### Endpoint

```
POST /api/v1/order/dossier_remove.json
```

### Update attachments

Updates the file attachments of an order. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/order/update_attachments.json
```

## Book entry

The following API endpoints are for managing order book entries. These are all the journal book entries that are created for an order (e.g. an invoice or a credit note), either automatically from items or manually by the user, like payments for example. Automatically created book entries cannot be manipulated directly, only by changing items (see [Orders](https://app.cashctrl.com/static/help/en/api/index.html#/order)).

### Read book entry

Returns a single book entry by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/bookentry/read.json
```

### List book entries

Returns a list of book entries for an order.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/bookentry/list.json
```

### Create book entry

Creates a new book entry. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `accountId` | mandatory, NUMBER | The ID of the account (e.g. a bank account). This is the contra account to the account defined in the order category (typically the debtors or creditors account). See [Account](https://app.cashctrl.com/static/help/en/api/index.html#/account). |
| `orderIds` | mandatory, CSV | The IDs of one or multiple orders, comma-separated. See [Order](https://app.cashctrl.com/static/help/en/api/index.html#/order). |
| `amount` | optional, NUMBER | The amount of the book entry (e.g. 125.50). Leave empty to use open amount of order. |
| `currencyId` | optional, NUMBER | The ID of the currency. Leave empty to use the default currency. See [Currency](https://app.cashctrl.com/static/help/en/api/index.html#/currency). |
| `currencyRate` | optional, NUMBER | The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested. |
| `date` | optional, DATE | The date of the book entry.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `description` | optional, TEXT, MAX:200 | The description of the book entry. |
| `reference` | optional, TEXT, MAX:100 | An optional reference / receipt for the book entry. |
| `taxId` | optional, NUMBER | The ID of the tax code. See [Tax codes](https://app.cashctrl.com/static/help/en/api/index.html#/tax). |
| `templateId` | optional, NUMBER | The ID of the book entry template. The templates are defined in the order category. See [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category). |

#### Endpoint

```
POST /api/v1/order/bookentry/create.json
```

### Update book entry

Updates an existing book entry. Note that you cannot update book entries that have been automatically created from order items, only manually created book entries (e.g. payments). Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `accountId` | mandatory, NUMBER | The ID of the account (e.g. a bank account). This is the contra account to the account defined in the order category (typically the debtors or creditors account). See [Account](https://app.cashctrl.com/static/help/en/api/index.html#/account). |
| `id` | mandatory, NUMBER | The ID of the book entry to update. |
| `amount` | optional, NUMBER | The amount of the book entry (e.g. 125.50). Leave empty to use open amount of order. |
| `currencyId` | optional, NUMBER | The ID of the currency. Leave empty to use the default currency. See [Currency](https://app.cashctrl.com/static/help/en/api/index.html#/currency). |
| `currencyRate` | optional, NUMBER | The exchange rate from foreign currency to main currency. Only required if the currency is not supported or if you want to use a different rate than suggested. |
| `date` | optional, DATE | The date of the book entry.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `description` | optional, TEXT, MAX:200 | The description of the book entry. |
| `reference` | optional, TEXT, MAX:100 | An optional reference / receipt for the book entry. |
| `taxId` | optional, NUMBER | The ID of the tax code. See [Tax codes](https://app.cashctrl.com/static/help/en/api/index.html#/tax). |
| `templateId` | optional, NUMBER | The ID of the book entry template. The templates are defined in the order category. See [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category). |

#### Endpoint

```
POST /api/v1/order/bookentry/update.json
```

### Delete book entries

Deletes one or multiple book entries. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/order/bookentry/delete.json
```

## Category

The following API endpoints are for managing order categories. An order category is for example 'Offers', 'Invoices', 'Delivery notes', etc. A category contains the configuration for the order document and how it behaves. It defines the different status a document can have, or whether the document creates journal book entries or not. You can add as many categories as you like and thus create your own workflow.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/category/read.json
```

### List categories

Returns a list of categories per type (sales or purchase).

#### Parameters

| | | |
| --- | --- | --- |
| `fiscalPeriodId` | optional, NUMBER | The ID of the fiscal period, from which we retrieve the counts (number of orders). Leave empty to use the current fiscal period. See [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json). |
| `type` | optional, TEXT | The type of category (sales orders or purchase orders). Defaults to SALES. Possible values: SALES, PURCHASE. |

#### Endpoint

```
GET /api/v1/order/category/list.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account, which is typically the debtors account for sales and the creditors account for purchase. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>namePlural</code></th><td>mandatory, TEXT, MAX:100</td><td>The plural name of the category (e.g. 'Invoices').<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>nameSingular</code></th><td>mandatory, TEXT, MAX:100</td><td>The singular name of the category (e.g. 'Invoice').<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>status</code></th><td>mandatory, JSON</td><td>The status list (like 'Draft', 'Open', 'Paid', etc.) for this order category. At least one status must exist.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>icon</code></th><td>mandatory, TEXT</td><td>The icon/color of the status. Possible values: BLUE, GREEN, RED, YELLOW, ORANGE, BLACK, GRAY, BROWN, VIOLET, PINK.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>The name of the status.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>actionId</code></th><td>optional, TEXT</td><td>An action associated with the status, i.e. what happens after I change the status to this? The action ID looks like this for example: CATEGORY_9. This would mean that another document of the order category with ID 9 will be created after changing to this status (CashCtrl asks the user first). The first part is either CATEGORY or BOOK_TEMPLATE. Then comes an underscore and the actual ID of the category or book template (e.g. BOOK_TEMPLATE_10).</td></tr>
<tr><th><code>isAddStock</code></th><td>optional, BOOLEAN</td><td>Whether inventory stock is added with this status. Note that when changing between two statuses that both have <code>isAddStock</code> set, it will only be added once, not twice. No matter how many times you change the status, it's only ever added once. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isBook</code></th><td>optional, BOOLEAN</td><td>Whether journal book entries will be created with this status. For example, the invoice status 'Draft' will not create any book entries, but all the other status after that ('Open', 'Paid', etc.) will. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isClosed</code></th><td>optional, BOOLEAN</td><td>Whether the status closes / completes the order object. This would be the case, for example, if an invoice has been fully paid. The effect is that the invoice is no longer due, even if past the due date (so no longer marked red). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isRemoveStock</code></th><td>optional, BOOLEAN</td><td>Whether inventory stock is removed with this status. Note that when changing between two statuses that both have <code>isRemoveStock</code> set, it will only be removed once, not twice. No matter how many times you change the status, it's only ever removed once. Defaults to false. Possible values: true, false.</td></tr>
</table>
</td></tr>
<tr><th><code>addressType</code></th><td>optional, TEXT</td><td>Which address of the recipient to use in the order document. Defaults to MAIN. Possible values: MAIN, INVOICE, DELIVERY, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>bookTemplates</code></th><td>optional, JSON</td><td>The book (entry) templates defined in this order category. An example of a book template for order categories would be the 'Payment' book template, which already has the appropriate bank account set, so that payments can be added with one click.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account in this book template. This is typically a bank account in case of a payment template, and it's the contra account to the account set on the order (debtors or creditors account). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>A name / description of the book template, which will be used as the description for the actual book entry. Example: 'Payment'.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>isAllowTax</code></th><td>optional, BOOLEAN</td><td>Whether the actual book entry will allow setting a tax rate. This is to prevent the user from making a mistake (e.g. for payment book entries). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code in this book template. This is only used if <code>isAllowTax</code> is true. For a payment book entry template you generally wouldn't allow setting a tax rate. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>bookType</code></th><td>optional, TEXT</td><td>Whether the account (see <code>accountId</code>) is on the debit or credit side in the book entry. Defaults to DEBIT. Possible values: DEBIT, CREDIT.</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency used by default for order objects in this category. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>dueDays</code></th><td>optional, NUMBER</td><td>The due days used by default for order objects in this category. The order date + due days equals the due date.</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>An optional PDF document whose pages are added at the end of the order document. Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>footerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the footer text used for order objects in this category.</td></tr>
<tr><th><code>hasDueDays</code></th><td>optional, BOOLEAN</td><td>Whether order objects in this category can have due days. The <code>dueDays</code> parameter is ignored if set to false. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>headerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the header text used for order objects in this category.</td></tr>
<tr><th><code>isDisplayItemGross</code></th><td>optional, BOOLEAN</td><td>Whether order item totals are displayed as gross (including tax) or net. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPrices</code></th><td>optional, BOOLEAN</td><td>Whether prices and totals are displayed on the document. For example a delivery note might not display prices, but an invoice does. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark category as inactive. Inactive categories are no longer displayed, but the documents in the category are not deleted. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isSwitchRecipient</code></th><td>optional, BOOLEAN</td><td>Switch recipient? By default your company is the sender and the client/vendor is the recipient. This flag switches sender and recipient. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>layoutId</code></th><td>optional, NUMBER</td><td>The ID of the layout used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/layout">Order layout</a>.</td></tr>
<tr><th><code>mailSubject</code></th><td>optional, TEXT, MAX:255</td><td>The mail subject (when sending the document via e-mail). Can contain variables.</td></tr>
<tr><th><code>mailTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the mail text used for order objects in this category.</td></tr>
<tr><th><code>message</code></th><td>optional, TEXT, MAX:50</td><td>A message for the payment recipient (included in the pain.001 xml file).</td></tr>
<tr><th><code>responsiblePersonId</code></th><td>optional, TEXT</td><td>The ID of the responsible person (Sachbearbeiter) used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>roundingId</code></th><td>optional, NUMBER</td><td>The ID of the rounding used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/rounding">Rounding</a>.</td></tr>
<tr><th><code>sentStatusId</code></th><td>optional, NUMBER</td><td>The ID of the status to automatically set when the order document is either sent by mail or downloaded. See <code>status</code> parameter. This can only be set if the category has already been saved, otherwise the status might not have an ID yet.</td></tr>
<tr><th><code>sequenceNrId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of category (sales orders or purchase orders). Defaults to SALES. Possible values: SALES, PURCHASE.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/order/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account, which is typically the debtors account for sales and the creditors account for purchase. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the category to update.</td></tr>
<tr><th><code>namePlural</code></th><td>mandatory, TEXT, MAX:100</td><td>The plural name of the category (e.g. 'Invoices').<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>nameSingular</code></th><td>mandatory, TEXT, MAX:100</td><td>The singular name of the category (e.g. 'Invoice').<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>status</code></th><td>mandatory, JSON</td><td>The status list (like 'Draft', 'Open', 'Paid', etc.) for this order category. At least one status must exist.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>icon</code></th><td>mandatory, TEXT</td><td>The icon/color of the status. Possible values: BLUE, GREEN, RED, YELLOW, ORANGE, BLACK, GRAY, BROWN, VIOLET, PINK.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>The name of the status.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>actionId</code></th><td>optional, TEXT</td><td>An action associated with the status, i.e. what happens after I change the status to this? The action ID looks like this for example: CATEGORY_9. This would mean that another document of the order category with ID 9 will be created after changing to this status (CashCtrl asks the user first). The first part is either CATEGORY or BOOK_TEMPLATE. Then comes an underscore and the actual ID of the category or book template (e.g. BOOK_TEMPLATE_10).</td></tr>
<tr><th><code>isAddStock</code></th><td>optional, BOOLEAN</td><td>Whether inventory stock is added with this status. Note that when changing between two statuses that both have <code>isAddStock</code> set, it will only be added once, not twice. No matter how many times you change the status, it's only ever added once. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isBook</code></th><td>optional, BOOLEAN</td><td>Whether journal book entries will be created with this status. For example, the invoice status 'Draft' will not create any book entries, but all the other status after that ('Open', 'Paid', etc.) will. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isClosed</code></th><td>optional, BOOLEAN</td><td>Whether the status closes / completes the order object. This would be the case, for example, if an invoice has been fully paid. The effect is that the invoice is no longer due, even if past the due date (so no longer marked red). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isRemoveStock</code></th><td>optional, BOOLEAN</td><td>Whether inventory stock is removed with this status. Note that when changing between two statuses that both have <code>isRemoveStock</code> set, it will only be removed once, not twice. No matter how many times you change the status, it's only ever removed once. Defaults to false. Possible values: true, false.</td></tr>
</table>
</td></tr>
<tr><th><code>addressType</code></th><td>optional, TEXT</td><td>Which address of the recipient to use in the order document. Defaults to MAIN. Possible values: MAIN, INVOICE, DELIVERY, SALARY, HISTORICAL, OTHER.</td></tr>
<tr><th><code>bookTemplates</code></th><td>optional, JSON</td><td>The book (entry) templates defined in this order category. An example of a book template for order categories would be the 'Payment' book template, which already has the appropriate bank account set, so that payments can be added with one click.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account in this book template. This is typically a bank account in case of a payment template, and it's the contra account to the account set on the order (debtors or creditors account). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>A name / description of the book template, which will be used as the description for the actual book entry. Example: 'Payment'.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>isAllowTax</code></th><td>optional, BOOLEAN</td><td>Whether the actual book entry will allow setting a tax rate. This is to prevent the user from making a mistake (e.g. for payment book entries). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>taxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code in this book template. This is only used if <code>isAllowTax</code> is true. For a payment book entry template you generally wouldn't allow setting a tax rate. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>bookType</code></th><td>optional, TEXT</td><td>Whether the account (see <code>accountId</code>) is on the debit or credit side in the book entry. Defaults to DEBIT. Possible values: DEBIT, CREDIT.</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency used by default for order objects in this category. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>dueDays</code></th><td>optional, NUMBER</td><td>The due days used by default for order objects in this category. The order date + due days equals the due date.</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>An optional PDF document whose pages are added at the end of the order document. Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>footerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the footer text used for order objects in this category.</td></tr>
<tr><th><code>hasDueDays</code></th><td>optional, BOOLEAN</td><td>Whether order objects in this category can have due days. The <code>dueDays</code> parameter is ignored if set to false. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>headerTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the header text used for order objects in this category.</td></tr>
<tr><th><code>isDisplayItemGross</code></th><td>optional, BOOLEAN</td><td>Whether order item totals are displayed as gross (including tax) or net. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPrices</code></th><td>optional, BOOLEAN</td><td>Whether prices and totals are displayed on the document. For example a delivery note might not display prices, but an invoice does. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark category as inactive. Inactive categories are no longer displayed, but the documents in the category are not deleted. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isSwitchRecipient</code></th><td>optional, BOOLEAN</td><td>Switch recipient? By default your company is the sender and the client/vendor is the recipient. This flag switches sender and recipient. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>layoutId</code></th><td>optional, NUMBER</td><td>The ID of the layout used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order/layout">Order layout</a>.</td></tr>
<tr><th><code>mailSubject</code></th><td>optional, TEXT, MAX:255</td><td>The mail subject (when sending the document via e-mail). Can contain variables.</td></tr>
<tr><th><code>mailTemplateId</code></th><td>optional, NUMBER</td><td>The ID of the mail text used for order objects in this category.</td></tr>
<tr><th><code>message</code></th><td>optional, TEXT, MAX:50</td><td>A message for the payment recipient (included in the pain.001 xml file).</td></tr>
<tr><th><code>responsiblePersonId</code></th><td>optional, TEXT</td><td>The ID of the responsible person (Sachbearbeiter) used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>roundingId</code></th><td>optional, NUMBER</td><td>The ID of the rounding used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/rounding">Rounding</a>.</td></tr>
<tr><th><code>sentStatusId</code></th><td>optional, NUMBER</td><td>The ID of the status to automatically set when the order document is either sent by mail or downloaded. See <code>status</code> parameter. This can only be set if the category has already been saved, otherwise the status might not have an ID yet.</td></tr>
<tr><th><code>sequenceNrId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used for order objects in this category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>type</code></th><td>optional, TEXT</td><td>The type of category (sales orders or purchase orders). Defaults to SALES. Possible values: SALES, PURCHASE.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/order/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/order/category/delete.json
```

### Reorder categories

Changes the order of one or multiple categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to reorder, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target entry. The entries (see `ids`) will be ordered before or after (see `before`) this entry. |
| `before` | optional, BOOLEAN | Reorder before the target entry, after otherwise. Defaults to true. Possible values: true, false. |
| `type` | optional, TEXT | The type of category. Defaults to SALES. Possible values: SALES, PURCHASE. |

#### Endpoint

```
POST /api/v1/order/category/reorder.json
```

### Read status

Returns a single status by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/category/read_status.json
```

## Document

The following API endpoints are for managing order documents. This API is not used to manage the order itself (like date, number, customer, items, etc.) - for that, see [Orders](https://app.cashctrl.com/static/help/en/api/index.html#/order). Here you only manage the sender / recipient of the document, which layout to use, and the document language. You can download the document as PDF or ZIP, and mail the document to the recipient.

### Read document

Returns a single document by order ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the order. |

#### Endpoint

```
GET /api/v1/order/document/read.json
```

### Download PDF

Downloads one or multiple order documents in one PDF file.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple orders, comma-separated. |

#### Endpoint

```
GET /api/v1/order/document/read.pdf
```

### Download ZIP

Downloads one or multiple order documents in a ZIP file (one PDF for each document).

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of one or multiple orders, comma-separated. |

#### Endpoint

```
GET /api/v1/order/document/read.zip
```

### Mail document

Sends a document per e-mail to the desired recipient(s).

#### Parameters

| | | |
| --- | --- | --- |
| `mailFrom` | mandatory, TEXT, MAX:255 | The sender / from e-mail address. |
| `mailSubject` | mandatory, TEXT, MAX:255 | The mail subject. Can contain variables. |
| `mailText` | mandatory, TEXT | The mail text. Can contain variables.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `orderIds` | mandatory, CSV | The IDs of the orders to send as mail, comma-separated. See [Order](https://app.cashctrl.com/static/help/en/api/index.html#/order). |
| `isCopyToMe` | optional, BOOLEAN | Send a copy to me? (the sender, see `mailFrom`) Possible values: true, false. |
| `mailBcc` | optional, TEXT | The BCC (blind carbon copy) e-mail address. You can enter multiple addresses comma-separated. |
| `mailCc` | optional, TEXT | The CC (carbon copy) e-mail address. You can enter multiple addresses comma-separated. |
| `mailTo` | optional, TEXT | The recipient e-mail address. You can enter multiple addresses comma-separated. Leave empty to use the default e-mail address of the business associate. |
| `sentStatusId` | optional, NUMBER | The ID of the status to set on the order after the mail has been sent. See [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category). |

#### Endpoint

```
POST /api/v1/order/document/mail.json
```

### Update document

Updates an existing document. To update the actual order object, see [Order](https://app.cashctrl.com/static/help/en/api/index.html#/order).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the order to update. See [Order](https://app.cashctrl.com/static/help/en/api/index.html#/order). |
| `customReference` | optional, TEXT | Custom Swiss QR reference or ISO-11649 reference which overrides the generated reference. Must be a valid reference. A Swiss QR reference can only be set, if a valid QR-IBAN is set, otherwise set an ISO-11649 reference. |
| `fileId` | optional, NUMBER | An optional PDF document whose pages are added at the end of the order document. Supported type: PDF. Max. size: 500KB. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |
| `footer` | optional, HTML | The text displayed below the items list on the document used by default for order objects in this category.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `header` | optional, HTML | The text displayed above the items list on the document used by default for order objects in this category.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `isDisplayItemGross` | optional, BOOLEAN | Whether order item totals are displayed as gross (including tax) or net. Defaults to false. Possible values: true, false. |
| `isFileReplacement` | optional, BOOLEAN | Replace the generated order document with the attached PDF file? (see `fileId`) Possible values: true, false. |
| `language` | optional, TEXT | The language of the document. Possible values: DE, EN, FR, IT. |
| `layoutId` | optional, NUMBER | The ID of the layout. See [Order layout](https://app.cashctrl.com/static/help/en/api/index.html#/order/layout). |
| `orgBankAccountId` | optional, NUMBER | The ID of the organization's bank account. See [Bank account](https://app.cashctrl.com/static/help/en/api/index.html#/account/bank). |
| `orgLocationId` | optional, NUMBER | The ID of the sender location. See [Location](https://app.cashctrl.com/static/help/en/api/index.html#/location). |
| `recipientAddressId` | optional, NUMBER | The ID of the recipient address (person address). See [Person](https://app.cashctrl.com/static/help/en/api/index.html#/person). |
| `recipientBankAccountId` | optional, NUMBER | The ID of the recipient's bank account. |

#### Endpoint

```
POST /api/v1/order/document/update.json
```

## Layout

The following API endpoints are for managing order layouts. Layouts define the look and feel of the [Order document](https://app.cashctrl.com/static/help/en/api/index.html#/order/document).

### Read layout

Returns a single layout by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/order/layout/read.json
```

### List layouts

Returns a list of all layouts.

#### Endpoint

```
GET /api/v1/order/layout/list.json
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
<tr><th><code>isDisplayDocumentName</code></th><td>optional, BOOLEAN</td><td>Display document name/title? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemArticleNr</code></th><td>optional, BOOLEAN</td><td>Display article no. for items? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemPriceRounded</code></th><td>optional, BOOLEAN</td><td>Display item prices rounded? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemTax</code></th><td>optional, BOOLEAN</td><td>Display tax for items? Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemUnit</code></th><td>optional, BOOLEAN</td><td>Display unit for items? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayLogo</code></th><td>optional, BOOLEAN</td><td>Display logo? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayOrgAddressInWindow</code></th><td>optional, BOOLEAN</td><td>Display (your) organization address in window? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPageNr</code></th><td>optional, BOOLEAN</td><td>Display page numbers? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPayments</code></th><td>optional, BOOLEAN</td><td>Display payments? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPosNr</code></th><td>optional, BOOLEAN</td><td>Display item numbering? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayRecipientNr</code></th><td>optional, BOOLEAN</td><td>Display recipient number (customer/vendor no.)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayResponsiblePerson</code></th><td>optional, BOOLEAN</td><td>Display responsible person (Sachbearbeiter)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayZeroTax</code></th><td>optional, BOOLEAN</td><td>Display zero tax (with a value of 0.00)? Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the layout as inactive. Inactive layouts are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>isOmitSameCountry</code></th><td>optional, BOOLEAN</td><td>Omit country, if same between sender/recipient? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isQrEmptyAmount</code></th><td>optional, BOOLEAN</td><td>Leave amount empty in the QR code? Otherwise the open amount is used in the QR code. Possible values: true, false.</td></tr>
<tr><th><code>isQrNoLines</code></th><td>optional, BOOLEAN</td><td>Display QR invoice without any lines? Dashed lines with scissors by default. Possible values: true, false.</td></tr>
<tr><th><code>isQrNoReferenceNr</code></th><td>optional, BOOLEAN</td><td>Display QR invoice without reference number? Generates reference number by default. Possible values: true, false.</td></tr>
<tr><th><code>letterPaperFileId</code></th><td>optional, NUMBER</td><td>An optional letter paper to embed on every page (behind the text). Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>logoHeight</code></th><td>optional, NUMBER, MIN:0.1, MAX:9.0</td><td>The height of the logo in centimeters.</td></tr>
<tr><th><code>pageSize</code></th><td>optional, TEXT</td><td>The page size of the document. Defaults to A4. Possible values: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, LEGAL, LETTER, A4R.</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent layout to inherit from. Letter paper, HTML and CSS will be inherited from the parent.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/order/layout/create.json
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
<tr><th><code>isDisplayDocumentName</code></th><td>optional, BOOLEAN</td><td>Display document name/title? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemArticleNr</code></th><td>optional, BOOLEAN</td><td>Display article no. for items? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemPriceRounded</code></th><td>optional, BOOLEAN</td><td>Display item prices rounded? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemTax</code></th><td>optional, BOOLEAN</td><td>Display tax for items? Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayItemUnit</code></th><td>optional, BOOLEAN</td><td>Display unit for items? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayLogo</code></th><td>optional, BOOLEAN</td><td>Display logo? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayOrgAddressInWindow</code></th><td>optional, BOOLEAN</td><td>Display (your) organization address in window? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPageNr</code></th><td>optional, BOOLEAN</td><td>Display page numbers? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPayments</code></th><td>optional, BOOLEAN</td><td>Display payments? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPosNr</code></th><td>optional, BOOLEAN</td><td>Display item numbering? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayRecipientNr</code></th><td>optional, BOOLEAN</td><td>Display recipient number (customer/vendor no.)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayResponsiblePerson</code></th><td>optional, BOOLEAN</td><td>Display responsible person (Sachbearbeiter)? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayZeroTax</code></th><td>optional, BOOLEAN</td><td>Display zero tax (with a value of 0.00)? Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the layout as inactive. Inactive layouts are greyed out and are no longer suggested. Possible values: true, false.</td></tr>
<tr><th><code>isOmitSameCountry</code></th><td>optional, BOOLEAN</td><td>Omit country, if same between sender/recipient? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isQrEmptyAmount</code></th><td>optional, BOOLEAN</td><td>Leave amount empty in the QR code? Otherwise the open amount is used in the QR code. Possible values: true, false.</td></tr>
<tr><th><code>isQrNoLines</code></th><td>optional, BOOLEAN</td><td>Display QR invoice without any lines? Dashed lines with scissors by default. Possible values: true, false.</td></tr>
<tr><th><code>isQrNoReferenceNr</code></th><td>optional, BOOLEAN</td><td>Display QR invoice without reference number? Generates reference number by default. Possible values: true, false.</td></tr>
<tr><th><code>letterPaperFileId</code></th><td>optional, NUMBER</td><td>An optional letter paper to embed on every page (behind the text). Supported type: PDF. Max. size: 500KB. Use the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File API</a> to upload a file and then use the file ID here.</td></tr>
<tr><th><code>logoHeight</code></th><td>optional, NUMBER, MIN:0.1, MAX:9.0</td><td>The height of the logo in centimeters.</td></tr>
<tr><th><code>pageSize</code></th><td>optional, TEXT</td><td>The page size of the document. Defaults to A4. Possible values: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, LEGAL, LETTER, A4R.</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent layout to inherit from. Letter paper, HTML and CSS will be inherited from the parent.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/order/layout/update.json
```

### Delete layouts

Deletes one or multiple layouts. Note that you cannot delete system layouts, only manually created ones. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/order/layout/delete.json
```

## Payment

The following API endpoints are for creating and downloading payment orders. Note that this does not create any book entries, for that see [Book entries](https://app.cashctrl.com/static/help/en/api/index.html#/order/bookentry). Here we are either creating an ISO 20022 pain.001 file or a PDF to download. The pain.001 file can be used in e-banking to automatically process multiple payments. Please first use the Create endpoint (don't skip this!), and then the Download endpoint.

### Create payment

Creates a new payment. This must first be executed before downloading the pain.001 or PDF file with the next endpoint, otherwise we won't be able to match the payments from a camt.052/053/054 file later on. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `date` | mandatory, DATE | The execution date for the payment.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `orderIds` | mandatory, CSV | The IDs of the selected orders, comma-separated. |
| `amount` | optional, NUMBER | A partial payment amount per order. Leave empty to pay all open amounts. |
| `isCombine` | optional, BOOLEAN | If set, merges multiple payments to the same payee into one transaction. Possible values: true, false. |
| `statusId` | optional, NUMBER | The ID of the new status for the order. |
| `type` | optional, TEXT | The type of payment and file to generate. Defaults to PAIN (pain.001). Possible values: PAIN, SEPA_PAIN, WIRE_PDF, CASH_PDF. |

#### Endpoint

```
POST /api/v1/order/payment/create.json
```

### Download file

Downloads the pain.001 or PDF file. Please use the create endpoint first, and then use the same parameters to download the file here. Returns a file.

#### Parameters

| | | |
| --- | --- | --- |
| `date` | mandatory, DATE | The execution date for the payment.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `orderIds` | mandatory, CSV | The IDs of the selected orders, comma-separated. |
| `amount` | optional, NUMBER | A partial payment amount per order. Leave empty to pay all open amounts. |
| `isCombine` | optional, BOOLEAN | If set, merges multiple payments to the same payee into one transaction. Possible values: true, false. |
| `statusId` | optional, NUMBER | The ID of the new status for the order. |
| `type` | optional, TEXT | The type of payment and file to generate. Defaults to PAIN (pain.001). Possible values: PAIN, SEPA_PAIN, WIRE_PDF, CASH_PDF. |

#### Endpoint

```
GET /api/v1/order/payment/download
```
