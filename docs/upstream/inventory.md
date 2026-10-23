Source: <https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article>\
Fetched: 2026-10-23 (UTC)

## Article

The following API endpoints are for managing articles. These are physical products that can have a stock, or services.

### Read article

Returns a single article by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/inventory/article/read.json
```

### List articles

Returns a list of articles.

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
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active articles. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyRestock</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles that need to be restocked. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'nr'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/article/list.json
```

### Export to Excel

Returns an Excel file of the entries list.

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
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active articles. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyRestock</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles that need to be restocked. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'nr'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/article/list.xlsx
```

### Export to CSV

Returns a CSV file of the entries list.

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
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active articles. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyRestock</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles that need to be restocked. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'nr'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/article/list.csv
```

### Export to PDF

Returns a PDF file of the entries list.

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
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active articles. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyCostCenters</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with cost centers. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyRestock</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles that need to be restocked. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only articles without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'nr'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/article/list.pdf
```

### Create article

Creates a new article. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:240</td><td>The name of the article.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>binLocation</code></th><td>optional, TEXT</td><td>The place within the building (e.g. A15, B04, C11, etc.) to locate the article. See <code>locationId</code>. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/category">Article category</a>.</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>A description of the article.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the article as inactive. The article will be greyed out. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isPurchasePriceGross</code></th><td>optional, BOOLEAN</td><td>The purchase price is net (excluding tax) by default. This defines the purchase price as gross (including tax). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isSalesPriceGross</code></th><td>optional, BOOLEAN</td><td>The sales price is net (excluding tax) by default. This defines the sales price as gross (including tax). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isStockArticle</code></th><td>optional, BOOLEAN</td><td>Whether the article has a stock, i.e. the stock should be tracked and updated via sales and purchase orders. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>lastPurchasePrice</code></th><td>optional, NUMBER</td><td>The last purchase price of the article. Net (excluding tax) by default, see <code>isPurchasePriceGross</code>. This price is automatically updated by purchase orders.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The ID of the location where the article can be found (e.g. a warehouse). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/location">Location</a>. Note that this represents the building whereas the <code>binLocation</code> parameter represents the place within the building. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>maxStock</code></th><td>optional, NUMBER</td><td>The desired maximum stock of the article. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>minStock</code></th><td>optional, NUMBER</td><td>The desired minimum stock of the article. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The article number. Leave empty to generate the number with <code>sequenceNumberId</code>.</td></tr>
<tr><th><code>salesPrice</code></th><td>optional, NUMBER</td><td>The sales price of the article. Net (excluding tax) by default, see <code>isSalesPriceGross</code>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the article number (see <code>nr</code>). If this is empty, the sequence number will not update when <code>nr</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>stock</code></th><td>optional, NUMBER</td><td>The current stock of the article. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>unitId</code></th><td>optional, TEXT</td><td>The ID of the unit (like pcs., meters, liters, etc.). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/unit">Units</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/article/create.json
```

### Update article

Updates an existing article. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the article to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:240</td><td>The name of the article.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>binLocation</code></th><td>optional, TEXT</td><td>The place within the building (e.g. A15, B04, C11, etc.) to locate the article. See <code>locationId</code>. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/category">Article category</a>.</td></tr>
<tr><th><code>currencyId</code></th><td>optional, NUMBER</td><td>The ID of the currency. Leave empty to use the default currency. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/currency">Currency</a>.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT</td><td>A description of the article.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the article as inactive. The article will be greyed out. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isPurchasePriceGross</code></th><td>optional, BOOLEAN</td><td>The purchase price is net (excluding tax) by default. This defines the purchase price as gross (including tax). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isSalesPriceGross</code></th><td>optional, BOOLEAN</td><td>The sales price is net (excluding tax) by default. This defines the sales price as gross (including tax). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>isStockArticle</code></th><td>optional, BOOLEAN</td><td>Whether the article has a stock, i.e. the stock should be tracked and updated via sales and purchase orders. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>lastPurchasePrice</code></th><td>optional, NUMBER</td><td>The last purchase price of the article. Net (excluding tax) by default, see <code>isPurchasePriceGross</code>. This price is automatically updated by purchase orders.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The ID of the location where the article can be found (e.g. a warehouse). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/location">Location</a>. Note that this represents the building whereas the <code>binLocation</code> parameter represents the place within the building. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>maxStock</code></th><td>optional, NUMBER</td><td>The desired maximum stock of the article. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>minStock</code></th><td>optional, NUMBER</td><td>The desired minimum stock of the article. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The article number. Leave empty to generate the number with <code>sequenceNumberId</code>.</td></tr>
<tr><th><code>salesPrice</code></th><td>optional, NUMBER</td><td>The sales price of the article. Net (excluding tax) by default, see <code>isSalesPriceGross</code>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the article number (see <code>nr</code>). If this is empty, the sequence number will not update when <code>nr</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
<tr><th><code>stock</code></th><td>optional, NUMBER</td><td>The current stock of the article. <code>isStockArticle</code> must be true, ignored otherwise.</td></tr>
<tr><th><code>unitId</code></th><td>optional, TEXT</td><td>The ID of the unit (like pcs., meters, liters, etc.). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/unit">Units</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/article/update.json
```

### Delete articles

Deletes one or multiple articles. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/inventory/article/delete.json
```

### Categorize articles

Assigns one or multiple articles to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/inventory/article/categorize.json
```

### Update attachments

Updates the file attachments of an article. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/inventory/article/update_attachments.json
```

## Article category

The following API endpoints are for managing article categories.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/inventory/article/category/read.json
```

### List categories

Returns a list of all categories.

#### Endpoint

```
GET /api/v1/inventory/article/category/list.json
```

### Get tree of categories

Returns a tree of all categories or the tree below a parent category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | Optional ID of the parent category (omit to get all categories). |

#### Endpoint

```
GET /api/v1/inventory/article/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers for all articles in this category. These will be used in order items, when selecting the article. If allocations are set here, they override any allocations that would be automatically made by the corresponding sales/purchase account.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent category.</td></tr>
<tr><th><code>purchaseAccountId</code></th><td>optional, NUMBER</td><td>The ID of the purchase account, which will be used when purchasing articles in this category through <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order">Orders</a>.</td></tr>
<tr><th><code>salesAccountId</code></th><td>optional, NUMBER</td><td>The ID of the sales account, which will be used when selling aticles in this category through <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order">Orders</a>.</td></tr>
<tr><th><code>sequenceNrId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used for services in this category. If empty, the sequence number of the parent category is inherited.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/article/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the category to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:100</td><td>The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>allocations</code></th><td>optional, JSON</td><td>Allocations to cost centers for all articles in this category. These will be used in order items, when selecting the article. If allocations are set here, they override any allocations that would be automatically made by the corresponding sales/purchase account.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>share</code></th><td>mandatory, NUMBER</td><td>Allocation share. For example, if you have two cost centers, and one has a share of 3, and the other has a share of 1, then the amount is allocated 3:1 (which equals 75% to 25%).</td></tr>
<tr><th><code>toCostCenterId</code></th><td>mandatory, NUMBER</td><td>ID of cost center to allocate to. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account/costcenter">Cost center</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>parentId</code></th><td>optional, NUMBER</td><td>The ID of the parent category.</td></tr>
<tr><th><code>purchaseAccountId</code></th><td>optional, NUMBER</td><td>The ID of the purchase account, which will be used when purchasing articles in this category through <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order">Orders</a>.</td></tr>
<tr><th><code>salesAccountId</code></th><td>optional, NUMBER</td><td>The ID of the sales account, which will be used when selling aticles in this category through <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order">Orders</a>.</td></tr>
<tr><th><code>sequenceNrId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used for services in this category. If empty, the sequence number of the parent category is inherited.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/article/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/inventory/article/category/delete.json
```

## Fixed asset

The following API endpoints are for managing fixed assets.

### Read fixed asset

Returns a single fixed asset by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/inventory/asset/read.json
```

### List fixed assets

Returns a list of fixed assets. Please first switch to the appropriate fiscal period to see the entries for that period only, see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the current values.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active fixed assets. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutDeprType</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without depreciation configured. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/asset/list.json
```

### Export to Excel

Returns an Excel file of the entries list. Please first switch to the appropriate fiscal period to see the entries for that period only, see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the current values.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active fixed assets. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutDeprType</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without depreciation configured. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/asset/list.xlsx
```

### Export to CSV

Returns a CSV file of the entries list. Please first switch to the appropriate fiscal period to see the entries for that period only, see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the current values.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active fixed assets. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutDeprType</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without depreciation configured. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/asset/list.csv
```

### Export to PDF

Returns a PDF file of the entries list. Please first switch to the appropriate fiscal period to see the entries for that period only, see [Switch fiscal period](https://app.cashctrl.com/static/help/en/api/index.html#/fiscalperiod/switch.json).

#### Parameters

<table>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>columns</code></th><td>optional, CSV</td><td>The columns to include in the list, comma-separated. Check the list.json for available column names.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>fiscalPeriodId</code></th><td>optional, NUMBER</td><td>The ID of the fiscal period, from which we retrieve the current values.</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>onlyActive</code></th><td>optional, BOOLEAN</td><td>Flag to include only active fixed assets. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithImages</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets with images. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutDeprType</code></th><td>optional, BOOLEAN</td><td>Flag to include only fixed assets without depreciation configured. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'dateAdded'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/inventory/asset/list.pdf
```

### Create fixed asset

Creates a new fixed asset. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account onto which the fixed asset is booked (e.g. Mobile assets). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateAdded</code></th><td>mandatory, DATE</td><td>The date when the fixed asset has been added.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:240</td><td>The name of the fixed asset.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>purchasePrice</code></th><td>mandatory, NUMBER</td><td>The initial purchase price of the fixed asset.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/asset/category">Fixed asset category</a>.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>dateDisposed</code></th><td>optional, DATE</td><td>The date of the disposal. Must be set if <code>disposalType</code> is set.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>deprAccountId</code></th><td>optional, NUMBER</td><td>The ID of the depreciation account (an expense account for depreciations). Must be set if <code>deprType</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>deprDuration</code></th><td>optional, NUMBER</td><td>The duration of the depreciation in years. Must be set if <code>deprType</code> is set.</td></tr>
<tr><th><code>deprSalvageValue</code></th><td>optional, NUMBER</td><td>The salvage value after depreciation is finished. This is the book value the fixed asset will retain afterwards. Defaults to 0.</td></tr>
<tr><th><code>deprType</code></th><td>optional, TEXT</td><td>The type of depreciation. Defaults to NONE (no deprecation). Possible values: NONE, LINEAR, DEGRESSIVE.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:512</td><td>A description of the fixed asset.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>disposalDebitId</code></th><td>optional, NUMBER</td><td>The ID of the account for the disposal (an expense account for disposals, similar to depreciation). Must be set if <code>disposalType</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>disposalType</code></th><td>optional, TEXT</td><td>The type of disposal. Defaults to NONE. Possible values: NONE, DIRECT, SALE_DIRECT.</td></tr>
<tr><th><code>initialValue</code></th><td>optional, NUMBER</td><td>The initial value of the fixed asset. If <code>purchaseType</code> is DIRECT, then this parameter will be ignored and the <code>purchasePrice</code> is used as initial value. This parameter is only used if the <code>purchaseType</code> is HISTORIC.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The ID of the location where the fixed asset can be found (e.g. a warehouse). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/location">Location</a>.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The article number. Leave empty to generate the number with <code>sequenceNumberId</code>, must be set otherwise.</td></tr>
<tr><th><code>purchaseCreditId</code></th><td>optional, NUMBER</td><td>The ID of the account for the fixed asset purchase (e.g. Bank account). Mandatory if <code>purchaseType</code> = DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>purchaseTaxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code for the purchase of the fixed asset. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>purchaseType</code></th><td>optional, TEXT</td><td>The type of purchase. Defaults to DIRECT. Possible values: DIRECT, HISTORICAL.</td></tr>
<tr><th><code>saleAmount</code></th><td>optional, NUMBER</td><td>The sale amount of the fixed asset, if the fixed asset has been sold. Must be set if <code>disposalType</code> is SALE_DIRECT.</td></tr>
<tr><th><code>saleCreditId</code></th><td>optional, NUMBER</td><td>The ID of the credit account for the sale of the fixed asset. Must be set if <code>disposalType</code> is SALE_DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>saleDebitId</code></th><td>optional, NUMBER</td><td>The ID of the debit account for the sale of the fixed asset. Must be set if <code>disposalType</code> is SALE_DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>saleTaxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code for the sale of the fixed asset. Can be set if <code>disposalType</code> is SALE_DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the article number (see <code>nr</code>). If this is empty, the sequence number will not update when <code>nr</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/asset/create.json
```

### Update fixed asset

Updates an existing fixed asset. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>The ID of the account onto which the fixed asset is booked (e.g. Mobile assets). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>dateAdded</code></th><td>mandatory, DATE</td><td>The date when the fixed asset has been added.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the fixed asset to update.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT, MAX:240</td><td>The name of the fixed asset.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>purchasePrice</code></th><td>mandatory, NUMBER</td><td>The initial purchase price of the fixed asset.</td></tr>
<tr><th><code>attachments</code></th><td>optional, JSON</td><td>List of files to attach.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>fileId</code></th><td>optional, NUMBER</td><td>ID of the file to attach. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/file">File</a>.</td></tr>
</table>
</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/asset/category">Fixed asset category</a>.</td></tr>
<tr><th><code>custom</code></th><td>optional, XML</td><td>Custom field values. They are stored as XML in this parameter. Example: <code>&lt;values&gt;&lt;customField1&gt;My value&lt;/customField1&gt;&lt;customField2&gt;["value 1","value 2"]&lt;/customField2&gt;&lt;/values&gt;</code>. Look up custom field variable names (e.g. "customField1") in the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/customfield">Custom fields</a> API.</td></tr>
<tr><th><code>dateDisposed</code></th><td>optional, DATE</td><td>The date of the disposal. Must be set if <code>disposalType</code> is set.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>deprAccountId</code></th><td>optional, NUMBER</td><td>The ID of the depreciation account (an expense account for depreciations). Must be set if <code>deprType</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>deprDuration</code></th><td>optional, NUMBER</td><td>The duration of the depreciation in years. Must be set if <code>deprType</code> is set.</td></tr>
<tr><th><code>deprSalvageValue</code></th><td>optional, NUMBER</td><td>The salvage value after depreciation is finished. This is the book value the fixed asset will retain afterwards. Defaults to 0.</td></tr>
<tr><th><code>deprType</code></th><td>optional, TEXT</td><td>The type of depreciation. Defaults to NONE (no deprecation). Possible values: NONE, LINEAR, DEGRESSIVE.</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:512</td><td>A description of the fixed asset.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>disposalDebitId</code></th><td>optional, NUMBER</td><td>The ID of the account for the disposal (an expense account for disposals, similar to depreciation). Must be set if <code>disposalType</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>disposalType</code></th><td>optional, TEXT</td><td>The type of disposal. Defaults to NONE. Possible values: NONE, DIRECT, SALE_DIRECT.</td></tr>
<tr><th><code>initialValue</code></th><td>optional, NUMBER</td><td>The initial value of the fixed asset. If <code>purchaseType</code> is DIRECT, then this parameter will be ignored and the <code>purchasePrice</code> is used as initial value. This parameter is only used if the <code>purchaseType</code> is HISTORIC.</td></tr>
<tr><th><code>locationId</code></th><td>optional, NUMBER</td><td>The ID of the location where the fixed asset can be found (e.g. a warehouse). See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/location">Location</a>.</td></tr>
<tr><th><code>notes</code></th><td>optional, HTML</td><td>Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration.</td></tr>
<tr><th><code>nr</code></th><td>optional, TEXT, MAX:50</td><td>The article number. Leave empty to generate the number with <code>sequenceNumberId</code>, must be set otherwise.</td></tr>
<tr><th><code>purchaseCreditId</code></th><td>optional, NUMBER</td><td>The ID of the account for the fixed asset purchase (e.g. Bank account). Mandatory if <code>purchaseType</code> = DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>purchaseTaxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code for the purchase of the fixed asset. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>purchaseType</code></th><td>optional, TEXT</td><td>The type of purchase. Defaults to DIRECT. Possible values: DIRECT, HISTORICAL.</td></tr>
<tr><th><code>saleAmount</code></th><td>optional, NUMBER</td><td>The sale amount of the fixed asset, if the fixed asset has been sold. Must be set if <code>disposalType</code> is SALE_DIRECT.</td></tr>
<tr><th><code>saleCreditId</code></th><td>optional, NUMBER</td><td>The ID of the credit account for the sale of the fixed asset. Must be set if <code>disposalType</code> is SALE_DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>saleDebitId</code></th><td>optional, NUMBER</td><td>The ID of the debit account for the sale of the fixed asset. Must be set if <code>disposalType</code> is SALE_DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>saleTaxId</code></th><td>optional, NUMBER</td><td>The ID of the tax code for the sale of the fixed asset. Can be set if <code>disposalType</code> is SALE_DIRECT. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/tax">Tax codes</a>.</td></tr>
<tr><th><code>sequenceNumberId</code></th><td>optional, NUMBER</td><td>The ID of the sequence number used to generate the article number (see <code>nr</code>). If this is empty, the sequence number will not update when <code>nr</code> is set. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/sequencenumber">Sequence number</a>.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/asset/update.json
```

### Delete fixed assets

Deletes one or multiple fixed assets. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/inventory/asset/delete.json
```

### Categorize fixed assets

Assigns one or multiple fixed assets to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/inventory/asset/categorize.json
```

### Update attachments

Updates the file attachments of a fixed asset. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |
| `fileIds` | optional, CSV | A list of file IDs, comma-separated. Leave empty to remove all attachments. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |

#### Endpoint

```
POST /api/v1/inventory/asset/update_attachments.json
```

## Fixed asset category

The following API endpoints are for managing fixed asset categories.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/inventory/asset/category/read.json
```

### List categories

Returns a list of all categories.

#### Endpoint

```
GET /api/v1/inventory/asset/category/list.json
```

### Get tree of categories

Returns a tree of all categories or the tree below a parent category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | Optional ID of the parent category (omit to get all categories). |

#### Endpoint

```
GET /api/v1/inventory/asset/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:100 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/inventory/asset/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the category to update. |
| `name` | mandatory, TEXT, MAX:100 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/inventory/asset/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/inventory/asset/category/delete.json
```

## Import

The following API endpoints are for importing articles from a file, either a vCard, Excel or CSV file.

### Create import

Creates a new import session. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `fileId` | mandatory, NUMBER | File to import. Valid formats: Excel and CSV. Max. size: 5 MB. Use the [File API](https://app.cashctrl.com/static/help/en/api/index.html#/file) to upload a file and then use the file ID here. |
| `categoryId` | optional, NUMBER | Category for all new articles, overriding imported categories. |

#### Endpoint

```
POST /api/v1/inventory/article/import/create.json
```

### Define mapping

Defines the mapping from Excel / CSV column header names to CashCtrl fields. See [List mapping fields](https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/mapping_combo.json) endpoint for a list of field names. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>Import session ID from the <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/create.json">Create</a> endpoint.</td></tr>
<tr><th><code>mapping</code></th><td>mandatory, JSON</td><td>Mapping from columns (Excel/CSV) to fields in CashCtrl.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>from</code></th><td>mandatory, TEXT</td><td>Column header name in Excel/CSV.</td></tr>
<tr><th><code>to</code></th><td>mandatory, TEXT</td><td>Field name in CashCtrl. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/mapping_combo.json">List mapping fields</a> endpoint for a list of field names.</td></tr>
</table>
</td></tr>
</table>

#### Endpoint

```
POST /api/v1/inventory/article/import/mapping.json
```

### List mapping fields

Lists the fields available in CashCtrl for mapping. Used in the [Define mapping](https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/mapping.json) endpoint.

#### Endpoint

```
GET /api/v1/inventory/article/import/mapping_combo.json
```

### Preview import

Previews the imported articles. Returns a list of articles that will be imported. This step can be omitted.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | Import session ID from the [Create](https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/create.json) endpoint. |

#### Endpoint

```
GET /api/v1/inventory/article/import/preview.json
```

### Execute import

Executes the importing of articles from the import session.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | Import session ID from the [Create](https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/create.json) endpoint. |
| `indexes` | optional, CSV | Index numbers of articles to import, comma-separated. All other articles are ignored. You can get the indexes from the JSON response of the [Preview](https://app.cashctrl.com/static/help/en/api/index.html#/inventory/article/import/preview) endpoint. Omit this parameter to import all articles. |

#### Endpoint

```
POST /api/v1/inventory/article/import/execute.json
```

## Unit

The following API endpoints are for managing units. A unit can be pcs., years, hours, meters, etc. The default unit is pcs.

### Read unit

Returns a single unit by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/inventory/unit/read.json
```

### List units

Returns a list of all units.

#### Endpoint

```
GET /api/v1/inventory/unit/list.json
```

### Create unit

Creates a new unit. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | optional, TEXT, MAX:100 | The name of the unit ('hours', 'minutes', etc.).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |

#### Endpoint

```
POST /api/v1/inventory/unit/create.json
```

### Update unit

Updates an existing unit. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the unit to update. |
| `name` | optional, TEXT, MAX:100 | The name of the unit ('hours', 'minutes', etc.).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |

#### Endpoint

```
POST /api/v1/inventory/unit/update.json
```

### Delete units

Deletes one or multiple units. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/inventory/unit/delete.json
```
