Source: <https://app.cashctrl.com/static/help/en/api/index.html#/file>\
Fetched: 2026-10-23 (UTC)

## File

The following API endpoints are for managing files. To upload a new file, you use the [Prepare files](https://app.cashctrl.com/static/help/en/api/index.html#/file/prepare.json) endpoint instead of the [Create file](https://app.cashctrl.com/static/help/en/api/index.html#/file/create.json) endpoint. See [Examples](https://app.cashctrl.com/static/help/en/api/index.html#example-file) for a tutorial on how to upload a file.

### Get file contents

Returns the contents (binary) of a single file by ID. Note that this will redirect to the actual file URL, as the CashCtrl main server does not deliver files. Be sure to handle redirects when using this endpoint. See [example](https://app.cashctrl.com/static/help/en/api/index.html#example-file-get).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/file/get
```

### Read file metadata

Returns the metadata of a single file by ID. Does not contain the file binary.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/file/read.json
```

### List files

Returns a list of files.

#### Parameters

<table>
<tr><th><code>archived</code></th><td>optional, BOOLEAN</td><td>Get archived files (only active files otherwise). Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to filter by.</td></tr>
<tr><th><code>dir</code></th><td>optional, TEXT</td><td>The direction of the sort order (ascending or descending). Defaults to 'DESC'. Possible values: ASC, DESC.</td></tr>
<tr><th><code>filter</code></th><td>optional, JSON</td><td>An array of filters to filter the list. All filters must match (AND).<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>comparison</code></th><td>optional, TEXT</td><td>Comparison type. Defaults to 'like'. Possible values: eq, like, gt, lt.</td></tr>
<tr><th><code>field</code></th><td>optional, TEXT</td><td>The name of the column to filter by.</td></tr>
<tr><th><code>value</code></th><td>optional, TEXT</td><td>Text to filter by, or a JSON array of multiple values (OR).</td></tr>
</table>
</td></tr>
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>mimeTypes</code></th><td>optional, CSV</td><td>Filter the file list by these mime types (comma-separated). For example, use image/* to filter by images only.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only files without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'lastUpdated'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>withoutSub</code></th><td>optional, BOOLEAN</td><td>Flag to exclude files in sub-categories. Defaults to false. Possible values: true, false.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/file/list.json
```

### Export to Excel

Returns an Excel file of the files list.

#### Parameters

<table>
<tr><th><code>archived</code></th><td>optional, BOOLEAN</td><td>Get archived files (only active files otherwise). Defaults to false. Possible values: true, false.</td></tr>
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
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>mimeTypes</code></th><td>optional, CSV</td><td>Filter the file list by these mime types (comma-separated). For example, use image/* to filter by images only.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only files without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'lastUpdated'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>withoutSub</code></th><td>optional, BOOLEAN</td><td>Flag to exclude files in sub-categories. Defaults to false. Possible values: true, false.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/file/list.xlsx
```

### Export to CSV

Returns a CSV file of the files list.

#### Parameters

<table>
<tr><th><code>archived</code></th><td>optional, BOOLEAN</td><td>Get archived files (only active files otherwise). Defaults to false. Possible values: true, false.</td></tr>
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
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>mimeTypes</code></th><td>optional, CSV</td><td>Filter the file list by these mime types (comma-separated). For example, use image/* to filter by images only.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only files without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'lastUpdated'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>withoutSub</code></th><td>optional, BOOLEAN</td><td>Flag to exclude files in sub-categories. Defaults to false. Possible values: true, false.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/file/list.csv
```

### Export to PDF

Returns a PDF file of the files list.

#### Parameters

<table>
<tr><th><code>archived</code></th><td>optional, BOOLEAN</td><td>Get archived files (only active files otherwise). Defaults to false. Possible values: true, false.</td></tr>
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
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>mimeTypes</code></th><td>optional, CSV</td><td>Filter the file list by these mime types (comma-separated). For example, use image/* to filter by images only.</td></tr>
<tr><th><code>onlyNotes</code></th><td>optional, BOOLEAN</td><td>Flag to only include entries with notes. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>onlyWithoutCategory</code></th><td>optional, BOOLEAN</td><td>Flag to include only files without a category. Defaults to false. Possible values: true, false.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>sort</code></th><td>optional, TEXT</td><td>The column to sort the list by. Defaults to 'lastUpdated'.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>withoutSub</code></th><td>optional, BOOLEAN</td><td>Flag to exclude files in sub-categories. Defaults to false. Possible values: true, false.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/file/list.pdf
```

### Prepare files

Prepares one or multiple files for uploading. This is the starting point for uploading files to CashCtrl. In this step, you only provide file metadata, not the actual file. Returns a list of file IDs and write URLs. Use the write URL to upload the file binary (using the PUT method). See the [Examples](https://app.cashctrl.com/static/help/en/api/index.html#example-file) for a tutorial on how to upload a file (prepare → put → persist).

#### Parameters

<table>
<tr><th><code>files</code></th><td>optional, JSON</td><td>The files to prepare.<br>This is a JSON array <code>[{...},{...},...]</code> with the following parameters:
<table>
<tr><th><code>mimeType</code></th><td>mandatory, TEXT</td><td>The mime type (content type) of the file. E.g. "application/pdf" for PDFs.</td></tr>
<tr><th><code>name</code></th><td>mandatory, TEXT</td><td>The file name. Must be a valid file name, but doesn't have to be unique.</td></tr>
<tr><th><code>categoryId</code></th><td>optional, NUMBER</td><td>The ID of the category to add the file in.</td></tr>
<tr><th><code>size</code></th><td>optional, NUMBER</td><td>The size of the file. This helps to determine early if the storage quota is exceeded or not. However, the actual file size will be determined later upon persisting the file.</td></tr>
</table>
</td></tr>
</table>

#### Endpoint

```
POST /api/v1/file/prepare.json
```

### Persist files

Persists one or multiple temporary files that have been prepared and uploaded. See [Prepare files](https://app.cashctrl.com/static/help/en/api/index.html#/file/prepare.json) endpoint.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/file/persist.json
```

### Create file

Creates a new file. This endpoint cannot be used to upload a new file. See [Prepare files](https://app.cashctrl.com/static/help/en/api/index.html#/file/prepare.json) endpoint. This endpoint makes an uploaded file permanent. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, TEXT | The ID of the uploaded temporary file. See [Prepare files](https://app.cashctrl.com/static/help/en/api/index.html#/file/prepare.json) endpoint. |
| `name` | mandatory, TEXT, MAX:255 | The file name. |
| `categoryId` | optional, NUMBER | The ID of the category. See [File category](https://app.cashctrl.com/static/help/en/api/index.html#/file/category). |
| `custom` | optional, XML | Custom field values. They are stored as XML in this parameter. Example: `<values><customField1>My value</customField1><customField2>["value 1","value 2"]</customField2></values>`. Look up custom field variable names (e.g. "customField1") in the [Custom fields](https://app.cashctrl.com/static/help/en/api/index.html#/customfield) API. |
| `description` | optional, TEXT, MAX:240 | A description for the file.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `notes` | optional, HTML | Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |

#### Endpoint

```
POST /api/v1/file/create.json
```

### Update file

Updates an existing file (only metadata, not binary). Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the file to update. |
| `name` | mandatory, TEXT, MAX:255 | The file name. |
| `categoryId` | optional, NUMBER | The ID of the category. See [File category](https://app.cashctrl.com/static/help/en/api/index.html#/file/category). |
| `custom` | optional, XML | Custom field values. They are stored as XML in this parameter. Example: `<values><customField1>My value</customField1><customField2>["value 1","value 2"]</customField2></values>`. Look up custom field variable names (e.g. "customField1") in the [Custom fields](https://app.cashctrl.com/static/help/en/api/index.html#/customfield) API. |
| `description` | optional, TEXT, MAX:240 | A description for the file.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `notes` | optional, HTML | Some optional notes.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |
| `replaceWith` | optional, NUMBER | Optionally replace the file binary (contents) with the binary from another file. Set the file ID here. That file must be a temporary file (not persisted yet). See [Prepare files](https://app.cashctrl.com/static/help/en/api/index.html#/file/prepare.json) endpoint. |

#### Endpoint

```
POST /api/v1/file/update.json
```

### Delete files

Deletes one or multiple files. This first archives the files (moves them to the recycle bin), unless `force` is set. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |
| `force` | optional, BOOLEAN | Force permanent deletion of file (do not archive first). Possible values: true, false. |

#### Endpoint

```
POST /api/v1/file/delete.json
```

### Categorize files

Assigns one or multiple files to the desired category. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to categorize, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target category. |

#### Endpoint

```
POST /api/v1/file/categorize.json
```

### Empty archive

Deletes all files that have been archived (moved to the recycle bin). Returns either a success or error message.

#### Endpoint

```
POST /api/v1/file/empty_archive.json
```

### Restore files

Restores one or multiple files that have been archived (moved to recycle bin). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/file/restore.json
```

## File category

The following API endpoints are for managing file categories.

### Read category

Returns a single category by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/file/category/read.json
```

### List categories

Returns a list of all categories.

#### Endpoint

```
GET /api/v1/file/category/list.json
```

### Get tree of categories

Returns a tree of all categories or the tree below a parent category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | optional, NUMBER | Optional ID of the parent category (omit to get all categories). |

#### Endpoint

```
GET /api/v1/file/category/tree.json
```

### Create category

Creates a new category. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:50 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/file/category/create.json
```

### Update category

Updates an existing category. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the category to update. |
| `name` | mandatory, TEXT, MAX:50 | The name of the category.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `parentId` | optional, NUMBER | The ID of the parent category. |

#### Endpoint

```
POST /api/v1/file/category/update.json
```

### Delete categories

Deletes one or multiple existing categories. Note that you can only delete empty categories. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/file/category/delete.json
```
