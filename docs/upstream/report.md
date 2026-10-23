Source: <https://app.cashctrl.com/static/help/en/api/index.html#/report>\
Fetched: 2026-10-23 (UTC)

## Report

The following API endpoint is for reading the report tree. This tree/list contains all of the instanced report collections with child elements and direct elements. A report collection is a collection of report elements which are grouped together and form one document, see [Report collection](https://app.cashctrl.com/static/help/en/api/index.html#/report/collection). A report element is the actual report, for example the balance sheet or profit and loss statement, see [Report element](https://app.cashctrl.com/static/help/en/api/index.html#/report/element).

### Get tree of reports

Returns a tree of all instanced reports containing collections and elements.

#### Endpoint

```
GET /api/v1/report/tree.json
```

## Collection

The following API endpoints are for managing report collections. Report collections can contain multiple report elements, which are the actual reports (see [Report element](https://app.cashctrl.com/static/help/en/api/index.html#/report/element)). So a report collection is basically like a group or a folder. A collection of reports can be viewed or downloaded as one document in PDF or other formats.

### Read collection

Returns a single collection by ID. This is the collection configuration and also returns all the report elements contained in this collection (their configuration, no data).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/report/collection/read.json
```

### Create collection

Creates a new collection. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:255</td><td>Name / title of the report collection.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>config</code></th><td>optional, JSON</td><td>Configuration options.<br>This is a JSON object <code>{...}</code> with the following parameters:
<table>
<tr><th><code>isDisplayFooter</code></th><td>optional, BOOLEAN</td><td>Display the footer on the PDF? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayHeader</code></th><td>optional, BOOLEAN</td><td>Display the header on the PDF? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayLogo</code></th><td>optional, BOOLEAN</td><td>Display the logo? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPeriodInTitle</code></th><td>optional, BOOLEAN</td><td>Display the time period in the title? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayTitle</code></th><td>optional, BOOLEAN</td><td>Display the title? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The location to be used for the logo and relevant placeholders in the text.</td></tr>
<tr><th><code>logoHeight</code></th><td>optional, NUMBER</td><td>The height of the logo in centimeters, as displayed on the report document (PDF).</td></tr>
<tr><th><code>pageSize</code></th><td>optional, TEXT</td><td>The page size of the report document (PDF). Defaults to A4. Possible values: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, LEGAL, LETTER, A4R.</td></tr>
<tr><th><code>responsiblePersonId</code></th><td>optional, NUMBER</td><td>The responsible person (used for placeholders in the text).</td></tr>
</table>
</td></tr>
<tr><th><code>text</code></th><td>optional, HTML</td><td>Text / description for the report collection.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/report/collection/create.json
```

### Update collection

Updates an existing collection. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the collection to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:255</td><td>Name / title of the report collection.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>config</code></th><td>optional, JSON</td><td>Configuration options.<br>This is a JSON object <code>{...}</code> with the following parameters:
<table>
<tr><th><code>isDisplayFooter</code></th><td>optional, BOOLEAN</td><td>Display the footer on the PDF? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayHeader</code></th><td>optional, BOOLEAN</td><td>Display the header on the PDF? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayLogo</code></th><td>optional, BOOLEAN</td><td>Display the logo? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayPeriodInTitle</code></th><td>optional, BOOLEAN</td><td>Display the time period in the title? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>isDisplayTitle</code></th><td>optional, BOOLEAN</td><td>Display the title? Defaults to true. Possible values: true, false.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The location to be used for the logo and relevant placeholders in the text.</td></tr>
<tr><th><code>logoHeight</code></th><td>optional, NUMBER</td><td>The height of the logo in centimeters, as displayed on the report document (PDF).</td></tr>
<tr><th><code>pageSize</code></th><td>optional, TEXT</td><td>The page size of the report document (PDF). Defaults to A4. Possible values: A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, LEGAL, LETTER, A4R.</td></tr>
<tr><th><code>responsiblePersonId</code></th><td>optional, NUMBER</td><td>The responsible person (used for placeholders in the text).</td></tr>
</table>
</td></tr>
<tr><th><code>text</code></th><td>optional, HTML</td><td>Text / description for the report collection.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/report/collection/update.json
```

### Delete collections

Deletes one or multiple collections. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/report/collection/delete.json
```

### Reorder collections

Changes the order of one or multiple collections. This is the order in which the report collections are displayed in the [Report tree](https://app.cashctrl.com/static/help/en/api/index.html#/report). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to reorder, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target entry. The entries (see `ids`) will be ordered before or after (see `before`) this entry. |
| `before` | optional, BOOLEAN | Reorder before the target entry, after otherwise. Defaults to true. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/report/collection/reorder.json
```

### Read meta data

Returns the meta data (title, text, etc.) of a single collection by ID for the given time period.

#### Parameters

| | | |
| --- | --- | --- |
| `collectionId` | mandatory, NUMBER | The ID of the collection. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/collection/meta.json
```

### Download PDF

Downloads the PDF file for a report collection by ID and time period.

#### Parameters

| | | |
| --- | --- | --- |
| `collectionId` | mandatory, NUMBER | The ID of the collection. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/collection/download.pdf
```

### Download CSV

Downloads a ZIP file containing the CSV files for a report collection by ID and time period.

#### Parameters

| | | |
| --- | --- | --- |
| `collectionId` | mandatory, NUMBER | The ID of the collection. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/collection/download.csv
```

### Download Excel

Downloads the Excel file for a report collection by ID and time period. Each report element is a worksheet within the Excel file.

#### Parameters

| | | |
| --- | --- | --- |
| `collectionId` | mandatory, NUMBER | The ID of the collection. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/collection/download.xlsx
```

### Download annual report

Downloads the PDF file for the annual report (balance sheet and profit and loss statement by default).

#### Parameters

| | | |
| --- | --- | --- |
| `fiscalPeriodId` | optional, NUMBER | The ID of the fiscal period. |

#### Endpoint

```
GET /api/v1/report/collection/download_annualreport.pdf
```

## Element

The following API endpoints are for managing report elements. Report elements are instances of report types like the balance sheet or the profit and loss statement. This means you can have multiple balance sheets with different configurations. Report elements can also be grouped together in sets, see [Report collection](https://app.cashctrl.com/static/help/en/api/index.html#/report/collection).

### Read element

Returns a single element by ID. This is the element configuration and does not contain any report data.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/report/element/read.json
```

### Create element

Creates a new element. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of the report. Possible values: JOURNAL, BALANCE, PLS, STAGGERED, COST_CENTER_PLS, COST_CENTER_BALANCE, COST_CENTER_ALLOCATION, COST_CENTER_TARGET, COST_CENTER_STATEMENTS, CHART_OF_ACCOUNTS, OPEN_DEBTORS, OPEN_CREDITORS, PEOPLE, ORG_CHART, TARGET, RESULT_BY_ARTICLE_PER_PERSON, EXPENSE_BY_PERSON, REVENUE_BY_PERSON, REVENUE_BY_RESPONSIBLE_PERSON, RESULT_BY_ARTICLE, STATEMENTS, BALANCE_LIST, KEY_FIGURES, EXPENSE_BY_PERSON_CHART, REVENUE_BY_PERSON_CHART, RESULT_BY_ARTICLE_CHART, BALANCE_PROG_CHART, BALANCE_SHARE_CHART, SALARY_BOOK_ENTRIES, SALARY_LIST, SALARY_TYPES, SALARY_TYPE_RECAP, SALARY_CONFIGURATION, SETTLEMENT, VAT_EVALUATION, VAT_JOURNAL, VAT_SETTLEMENT, WITHHOLDING_TAX_SETTLEMENT, WITHHOLDING_TAX_RATES, CASH_FLOW_CHART, TEXT_IMAGE.</td></tr>
<tr><th><code>collectionId</code></th><td>optional, NUMBER</td><td>Optional ID of a report collection, to include this element in the collection.</td></tr>
<tr><th><code>columns</code></th><td>optional, JSON</td><td>Columns to display, for reports with dynamic columns (not every report).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>title</code></th><td>mandatory, TEXT</td><td>The title / heading of the column.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>calculation</code></th><td>optional, TEXT</td><td>The value of a custom column can be calculated with variables from other columns. Example: "$price * $quantity". Only if fieldName is empty, ignored otherwise.</td></tr>
<tr><th><code>fieldName</code></th><td>optional, TEXT</td><td>Name of an existing field (e.g. 'firstName', 'lastName') or a custom field (e.g. 'customField24'). Leave empty to create a custom calculation column.</td></tr>
<tr><th><code>variable</code></th><td>optional, TEXT</td><td>An optional variable name for use in further calculations. Must be alphanumeric and start with a '$'. Example: $myVariable. Only if fieldName is empty, ignored otherwise.</td></tr>
</table>
</td></tr>
<tr><th><code>config</code></th><td>optional, JSON</td><td>Configuration options specific for each report type. We cannot document all possible configuration options here, but you can check the parameters that CashCtrl sends when saving a report config in the browser's developer console (Network tab).<br>This is a JSON object <code>{...}</code>.</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>File associated with the report element (e.g. image for the 'Text &amp; Image' report).</td></tr>
<tr><th><code>isHideTitle</code></th><td>optional, BOOLEAN</td><td>Hide title of the report. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isPageBreak</code></th><td>optional, BOOLEAN</td><td>Page break before the report (for PDF). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>name</code></th><td>optional, TEXT, MAX:50</td><td>Name / title of the report.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>text</code></th><td>optional, HTML</td><td>Text / description for the report.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/report/element/create.json
```

### Update element

Updates an existing element. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the element to update.</td></tr>
<tr><th><code>type</code></th><td>mandatory, TEXT</td><td>The type of the report. Possible values: JOURNAL, BALANCE, PLS, STAGGERED, COST_CENTER_PLS, COST_CENTER_BALANCE, COST_CENTER_ALLOCATION, COST_CENTER_TARGET, COST_CENTER_STATEMENTS, CHART_OF_ACCOUNTS, OPEN_DEBTORS, OPEN_CREDITORS, PEOPLE, ORG_CHART, TARGET, RESULT_BY_ARTICLE_PER_PERSON, EXPENSE_BY_PERSON, REVENUE_BY_PERSON, REVENUE_BY_RESPONSIBLE_PERSON, RESULT_BY_ARTICLE, STATEMENTS, BALANCE_LIST, KEY_FIGURES, EXPENSE_BY_PERSON_CHART, REVENUE_BY_PERSON_CHART, RESULT_BY_ARTICLE_CHART, BALANCE_PROG_CHART, BALANCE_SHARE_CHART, SALARY_BOOK_ENTRIES, SALARY_LIST, SALARY_TYPES, SALARY_TYPE_RECAP, SALARY_CONFIGURATION, SETTLEMENT, VAT_EVALUATION, VAT_JOURNAL, VAT_SETTLEMENT, WITHHOLDING_TAX_SETTLEMENT, WITHHOLDING_TAX_RATES, CASH_FLOW_CHART, TEXT_IMAGE.</td></tr>
<tr><th><code>collectionId</code></th><td>optional, NUMBER</td><td>Optional ID of a report collection, to include this element in the collection.</td></tr>
<tr><th><code>columns</code></th><td>optional, JSON</td><td>Columns to display, for reports with dynamic columns (not every report).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>title</code></th><td>mandatory, TEXT</td><td>The title / heading of the column.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>calculation</code></th><td>optional, TEXT</td><td>The value of a custom column can be calculated with variables from other columns. Example: "$price * $quantity". Only if fieldName is empty, ignored otherwise.</td></tr>
<tr><th><code>fieldName</code></th><td>optional, TEXT</td><td>Name of an existing field (e.g. 'firstName', 'lastName') or a custom field (e.g. 'customField24'). Leave empty to create a custom calculation column.</td></tr>
<tr><th><code>variable</code></th><td>optional, TEXT</td><td>An optional variable name for use in further calculations. Must be alphanumeric and start with a '$'. Example: $myVariable. Only if fieldName is empty, ignored otherwise.</td></tr>
</table>
</td></tr>
<tr><th><code>config</code></th><td>optional, JSON</td><td>Configuration options specific for each report type. We cannot document all possible configuration options here, but you can check the parameters that CashCtrl sends when saving a report config in the browser's developer console (Network tab).<br>This is a JSON object <code>{...}</code>.</td></tr>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>File associated with the report element (e.g. image for the 'Text &amp; Image' report).</td></tr>
<tr><th><code>isHideTitle</code></th><td>optional, BOOLEAN</td><td>Hide title of the report. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isPageBreak</code></th><td>optional, BOOLEAN</td><td>Page break before the report (for PDF). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>name</code></th><td>optional, TEXT, MAX:50</td><td>Name / title of the report.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>text</code></th><td>optional, HTML</td><td>Text / description for the report.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/report/element/update.json
```

### Delete elements

Deletes one or multiple elements. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/report/element/delete.json
```

### Reorder elements

Changes the order of one or multiple elements. This is the order in which the report elements are displayed in the [Report tree](https://app.cashctrl.com/static/help/en/api/index.html#/report). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to reorder, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target entry. The entries (see `ids`) will be ordered before or after (see `before`) this entry. |
| `before` | optional, BOOLEAN | Reorder before the target entry, after otherwise. Defaults to true. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/report/element/reorder.json
```

### Read JSON data

Returns the JSON data of a single element by ID for the given time period.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/data.json
```

### Read HTML data

Returns the HTML data of a single element by ID for the given time period.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/data.html
```

### Read meta data

Returns the JSON meta data (title, text, etc.) of a single element by ID for the given time period.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/meta.json
```

### Download PDF

Downloads the PDF file for a single element by ID and time period.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/download.pdf
```

### Download CSV

Downloads the CSV file for a single element by ID and time period.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/download.csv
```

### Download Excel

Downloads the Excel file for a single element by ID and time period.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/download.xlsx
```

### Download XML

Downloads the XML file for a single element by ID and time period. Note that this is not available for most reports, only where an XML representation exists (e.g. the VAT settlement report). Also, this endpoint is validated, so you might get validation errors instead of the XML report.

#### Parameters

| | | |
| --- | --- | --- |
| `elementId` | mandatory, NUMBER | The ID of the element. |
| `endDate` | optional, DATE | The end date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |
| `fiscalPeriod` | optional, NUMBER | The ID of the fiscal period. This overrides the `startDate` and `endDate` parameter, as these are derived from the fiscal period. See [Fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod). |
| `language` | optional, TEXT | The language of the report. |
| `sort` | optional, TEXT | The column to sort the list by. |
| `startDate` | optional, DATE | The start date of the report period.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/report/element/download.xml
```
