Source: <https://app.cashctrl.com/static/help/en/api/index.html#/currency>

## Currency

The following API endpoints are for managing currencies.

### Read currency

Returns a single currency by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/currency/read.json
```

### List currencies

Returns a list of all currencies.

#### Endpoint

```
GET /api/v1/currency/list.json
```

### Create currency

Creates a new currency. The currency code must be unique. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `code` | mandatory, TEXT, MIN:3, MAX:3 | The 3-characters currency code, like CHF, EUR, etc. |
| `description` | optional, TEXT, MAX:50 | An optional description of the currency.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `isDefault` | optional, BOOLEAN | Use the currency as the default / main currency. This can only be set if there are no book entries yet. Defaults to false. Possible values: true, false. |
| `rate` | optional, NUMBER | The exchange rate of this currency into the default currency. If this currency is the default currency, then the rate is 1. For most currencies, CashCtrl automatically retrieves the exchange rate, so this doesn't have to be set and will be ignored. Only set the rate for unsupported currencies. For supported currencies, see [Get exchange rate](https://app.cashctrl.com/static/help/en/api/index.html#/currency/exchangerate). |

#### Endpoint

```
POST /api/v1/currency/create.json
```

### Update currency

Updates an existing currency. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `code` | mandatory, TEXT, MIN:3, MAX:3 | The 3-characters currency code, like CHF, EUR, etc. |
| `id` | mandatory, NUMBER | The ID of the currency to update. |
| `description` | optional, TEXT, MAX:50 | An optional description of the currency.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `isDefault` | optional, BOOLEAN | Use the currency as the default / main currency. This can only be set if there are no book entries yet. Defaults to false. Possible values: true, false. |
| `rate` | optional, NUMBER | The exchange rate of this currency into the default currency. If this currency is the default currency, then the rate is 1. For most currencies, CashCtrl automatically retrieves the exchange rate, so this doesn't have to be set and will be ignored. Only set the rate for unsupported currencies. For supported currencies, see [Get exchange rate](https://app.cashctrl.com/static/help/en/api/index.html#/currency/exchangerate). |

#### Endpoint

```
POST /api/v1/currency/update.json
```

### Delete currencies

Deletes one or multiple currencies. Only unused currencies can be deleted, and the main currency cannot be deleted (switch first). Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/currency/delete.json
```

### Get exchange rate

Returns the exchange rate between two currencies for a specific date.

#### Parameters

| | | |
| --- | --- | --- |
| `from` | mandatory, TEXT | The source currency to convert. Possible values: AUD, BTC, CAD, CHF, CNY, DKK, EUR, GBP, INR, JPY, PLN, RUB, SEK, THB, USD. |
| `to` | mandatory, TEXT | The target currency to convert into. Possible values: AUD, BTC, CAD, CHF, CNY, DKK, EUR, GBP, INR, JPY, PLN, RUB, SEK, THB, USD. |
| `date` | optional, DATE | The date for the exchange rate. Leave empty to use today.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/currency/exchangerate
```

## Custom field

The following API endpoints are for managing custom fields. An infinite number of custom fields can be defined for all main modules (Journal, Account, Inventory, Order, Person).

### Read custom field

Returns a single custom field by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/customfield/read.json
```

### List custom fields

Returns a list of custom fields by type.

#### Parameters

| | | |
| --- | --- | --- |
| `type` | mandatory, TEXT | The type of custom field, meaning: which module the custom field belongs to. Possible values: JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, SALARY_STATEMENT. |

#### Endpoint

```
GET /api/v1/customfield/list.json
```

### Create custom field

Creates a new custom field for the given type. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `dataType` | mandatory, TEXT | The data type of the custom field. Possible values: TEXT, TEXTAREA, CHECKBOX, DATE, COMBOBOX, NUMBER, ACCOUNT, PERSON. |
| `rowLabel` | mandatory, TEXT, MAX:100 | Label displayed left of the field. If multiple custom fields have the same `rowLabel`, they will be displayed on the same row.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `type` | mandatory, TEXT | The type of custom field, meaning: which module the custom field belongs to. Possible values: JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, SALARY_STATEMENT. |
| `fieldInfo` | optional, TEXT, MAX:240 | An optional description of the custom field (displayed by hovering over an info icon).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `fieldLabel` | optional, TEXT, MAX:100 | Smaller label displayed above the field.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `fieldTextRight` | optional, TEXT, MAX:20 | Optional text displayed right of the field.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `groupId` | optional, TEXT | The ID of the custom field group. If empty, the custom field is in the default group 'More'. Groups are basically displayed as tabs in the edit dialog, whereas the default tab is 'More'. |
| `isInactive` | optional, BOOLEAN | Mark the custom field as inactive. Inactive custom fields are no longer displayed anywhere. However, the data is not removed, as opposed to deleting the custom field. Defaults to false. Possible values: true, false. |
| `isMulti` | optional, BOOLEAN | Is the custom field a multi-field? Multi-fields can have multiple values. The data is then stored as JSON array, like for example `["val1", "val2", "val3"]`. Defaults to false. Possible values: true, false. |
| `maxWidth` | optional, NUMBER, MIN:30.0 | The maximum width of the field. By default, the field width is stretched. |
| `values` | optional, TEXT | Values the user can choose from, if the data type is COMBOBOX. Ignored otherwise. Use the JSON format like this: `["red","green","blue"]`. Note that these values are not enforced, the user can still set arbitrary text as the custom field value. |
| `variableName` | optional, TEXT, MAX:32 | An optional, more meaningful variable name, instead of the default $customField\<ID> variable name. Must start with a `$` and contain only alphanumeric characters. |

#### Endpoint

```
POST /api/v1/customfield/create.json
```

### Update custom field

Updates an existing custom field. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `dataType` | mandatory, TEXT | The data type of the custom field. Possible values: TEXT, TEXTAREA, CHECKBOX, DATE, COMBOBOX, NUMBER, ACCOUNT, PERSON. |
| `id` | mandatory, NUMBER | The ID of the custom field to update. |
| `rowLabel` | mandatory, TEXT, MAX:100 | Label displayed left of the field. If multiple custom fields have the same `rowLabel`, they will be displayed on the same row.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `type` | mandatory, TEXT | The type of custom field, meaning: which module the custom field belongs to. Possible values: JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, SALARY_STATEMENT. |
| `fieldInfo` | optional, TEXT, MAX:240 | An optional description of the custom field (displayed by hovering over an info icon).<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `fieldLabel` | optional, TEXT, MAX:100 | Smaller label displayed above the field.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `fieldTextRight` | optional, TEXT, MAX:20 | Optional text displayed right of the field.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `groupId` | optional, TEXT | The ID of the custom field group. If empty, the custom field is in the default group 'More'. Groups are basically displayed as tabs in the edit dialog, whereas the default tab is 'More'. |
| `isInactive` | optional, BOOLEAN | Mark the custom field as inactive. Inactive custom fields are no longer displayed anywhere. However, the data is not removed, as opposed to deleting the custom field. Defaults to false. Possible values: true, false. |
| `isMulti` | optional, BOOLEAN | Is the custom field a multi-field? Multi-fields can have multiple values. The data is then stored as JSON array, like for example `["val1", "val2", "val3"]`. Defaults to false. Possible values: true, false. |
| `maxWidth` | optional, NUMBER, MIN:30.0 | The maximum width of the field. By default, the field width is stretched. |
| `values` | optional, TEXT | Values the user can choose from, if the data type is COMBOBOX. Ignored otherwise. Use the JSON format like this: `["red","green","blue"]`. Note that these values are not enforced, the user can still set arbitrary text as the custom field value. |
| `variableName` | optional, TEXT, MAX:32 | An optional, more meaningful variable name, instead of the default $customField\<ID> variable name. Must start with a `$` and contain only alphanumeric characters. |

#### Endpoint

```
POST /api/v1/customfield/update.json
```

### Delete custom field

Deletes one or multiple custom fields. Note that you can delete custom fields even if they hava data. All data of deleted custom fields will be lost. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/customfield/delete.json
```

### Reorder custom fields

Changes the order of one or multiple custom fields. This is the order in which the custom fields are displayed. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to reorder, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target entry. The entries (see `ids`) will be ordered before or after (see `before`) this entry. |
| `before` | optional, BOOLEAN | Reorder before the target entry, after otherwise. Defaults to true. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/customfield/reorder.json
```

### Get custom field types

Returns a list of custom field types, with `type` and `i18nKey`.

#### Endpoint

```
GET /api/v1/customfield/types.json
```

## Custom field group

The following API endpoints are for managing custom field groups. A group is displayed as a tab in the edit dialog (e.g. of an article), and you can have multiple such tabs to maintain a tidy UI. Custom fields that do not have a group go in a tab named 'More' by default.

### Read custom field group

Returns a single custom field group by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/customfield/group/read.json
```

### List custom field groups

Returns a list of custom field groups.

#### Parameters

| | | |
| --- | --- | --- |
| `type` | mandatory, TEXT | The type of custom field group, meaning: which module the custom field group belongs to. Possible values: JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, SALARY_STATEMENT. |

#### Endpoint

```
GET /api/v1/customfield/group/list.json
```

### Create custom field group

Creates a new custom field group. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:50 | The name of the group.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `type` | mandatory, TEXT | The type of group, meaning: which module the group belongs to. Possible values: JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, SALARY_STATEMENT. |

#### Endpoint

```
POST /api/v1/customfield/group/create.json
```

### Update custom field group

Updates an existing custom field group. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the group to update. |
| `name` | mandatory, TEXT, MAX:50 | The name of the group.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `type` | mandatory, TEXT | The type of group, meaning: which module the group belongs to. Possible values: JOURNAL, ACCOUNT, INVENTORY_ARTICLE, INVENTORY_ASSET, ORDER, PERSON, FILE, SALARY_STATEMENT. |

#### Endpoint

```
POST /api/v1/customfield/group/update.json
```

### Delete custom field group

Deletes one or multiple custom field groups. This does not delete any custom fields, and no data will be lost. The custom fields in that group just won't have a group anymore and will be displayed in the default 'More' tab. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/customfield/group/delete.json
```

### Reorder custom field groups

Changes the order of one or multiple custom field groups. This is the order in which the tabs are displayed in the edit dialog. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the entries to reorder, comma-separated. |
| `target` | mandatory, NUMBER | The ID of the target entry. The entries (see `ids`) will be ordered before or after (see `before`) this entry. |
| `before` | optional, BOOLEAN | Reorder before the target entry, after otherwise. Defaults to true. Possible values: true, false. |

#### Endpoint

```
POST /api/v1/customfield/group/reorder.json
```

## History

The following API endpoints are for retrieving the history / audit log.

### List history

Returns the history list.

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
<tr><th><code>limit</code></th><td>optional, NUMBER</td><td>The number of entries to retrieve. Defaults to 100.</td></tr>
<tr><th><code>orderId</code></th><td>optional, NUMBER</td><td>ID of order to retrieve the history for. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/order">Order</a>.</td></tr>
<tr><th><code>personId</code></th><td>optional, NUMBER</td><td>ID of person to retrieve the history for. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/person">Person</a>.</td></tr>
<tr><th><code>query</code></th><td>optional, TEXT</td><td>Fulltext search query.</td></tr>
<tr><th><code>start</code></th><td>optional, NUMBER</td><td>The starting entry. Defaults to 0.</td></tr>
<tr><th><code>statementId</code></th><td>optional, NUMBER</td><td>ID of salary statement to retrieve the history for. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/salary/statement">Salary statement</a>.</td></tr>
</table>

#### Endpoint

```
GET /api/v1/history/list.json
```

## Rounding

The following API endpoints are for managing roundings. These rounding configurations are mainly used for rounding the grand total of orders (invoices, etc.).

### Read rounding

Returns a single rounding by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/rounding/read.json
```

### List roundings

Returns a list of all roundings.

#### Endpoint

```
GET /api/v1/rounding/list.json
```

### Create rounding

Creates a new rounding. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `accountId` | mandatory, NUMBER | The ID of the account onto which the rounding amount is booked. |
| `name` | mandatory, TEXT, MAX:100 | A name to describe the rounding method (e.g. 'Round to 0.05').<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `rounding` | mandatory, NUMBER, MIN:0.0 | The rounding amount (e.g. 0.05 to round to five cents). |
| `mode` | optional, TEXT | The rounding mode. Defaults to HALF_UP. Possible values: UP, DOWN, CEILING, FLOOR, HALF_UP, HALF_DOWN, HALF_EVEN, UNNECESSARY. |

#### Endpoint

```
POST /api/v1/rounding/create.json
```

### Update rounding

Updates an existing rounding. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `accountId` | mandatory, NUMBER | The ID of the account onto which the rounding amount is booked. |
| `id` | mandatory, NUMBER | The ID of the rounding to update. |
| `name` | mandatory, TEXT, MAX:100 | A name to describe the rounding method (e.g. 'Round to 0.05').<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `rounding` | mandatory, NUMBER, MIN:0.0 | The rounding amount (e.g. 0.05 to round to five cents). |
| `mode` | optional, TEXT | The rounding mode. Defaults to HALF_UP. Possible values: UP, DOWN, CEILING, FLOOR, HALF_UP, HALF_DOWN, HALF_EVEN, UNNECESSARY. |

#### Endpoint

```
POST /api/v1/rounding/update.json
```

### Delete roundings

Deletes one or multiple roundings. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/rounding/delete.json
```

## Sequence number

The following API endpoints are for managing sequence numbers. Sequence numbers are used for generating new numbers for journal entries (reference / receipt no.), inventory articles (article no.), orders (invoice no., etc.) and people (customer/vendor no.).

### Read sequence number

Returns a single sequence number by ID or type and optionally category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the sequence number. Either `id` or `type` must be set. |
| `type` | mandatory, TEXT | The type of the sequence number, meaning: which module the sequence number belongs to. Either `id` or `type` must be set. Possible values: INVENTORY_ARTICLE, INVENTORY_ASSET, JOURNAL, ORDER, PERSON, SALARY. |
| `categoryId` | optional, NUMBER | Optional ID of the category where a sequence number is defined. This only works together with the `type` parameter. For example if the `type` is PERSON and the `categoryId` the ID of a person category, you'll retrieve the sequence number defined in that category (if defined). |
| `date` | optional, DATE | An optional date, which will influence the next sequence number to be generated.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/sequencenumber/read.json
```

### Get generated number

Returns the next generated number for the given ID or type and optionally category.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the sequence number. Either `id` or `type` must be set. |
| `type` | mandatory, TEXT | The type of the sequence number, meaning: which module the sequence number belongs to. Either `id` or `type` must be set. Possible values: INVENTORY_ARTICLE, INVENTORY_ASSET, JOURNAL, ORDER, PERSON, SALARY. |
| `categoryId` | optional, NUMBER | Optional ID of the category where a sequence number is defined. This only works together with the `type` parameter. For example if the `type` is PERSON and the `categoryId` the ID of a person category, you'll retrieve the sequence number defined in that category (if defined). |
| `date` | optional, DATE | An optional date, which will influence the next sequence number to be generated.<br>Format: YYYY-MM-DD. Example: `2020-01-15`. |

#### Endpoint

```
GET /api/v1/sequencenumber/get
```

### List sequence numbers

Returns a list of all sequence numbers.

#### Endpoint

```
GET /api/v1/sequencenumber/list.json
```

### Create sequence number

Creates a new sequence number. Note that you cannot assign the sequence number to a type (e.g. Journal) here, this is done in the [Settings](https://app.cashctrl.com/static/help/en/api/index.html#/setting) or in the corresponding category (e.g. [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category)). Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:100 | A name to describe and identify the sequence number.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `pattern` | mandatory, TEXT, MAX:50 | The sequence number pattern, which consists of variables and arbitrary text from which a sequence number will be generated. Possible variables: $y = Current year. $m = Current month. $d = Current day. $ny = Sequence number, resets annually (on Jan 1st). $nm = Sequence number, resets monthly. $nd = Sequence number, resets daily. $nn = Sequence number, never resets. Example pattern: `RE-$y$m$d$nd` which may generate 'RE-2007151' (on July 15, 2020). |
| `currentDailyNumber` | optional, NUMBER | The current value of the daily number (variable $nd). Defaults to 1. |
| `currentInfiniteNumber` | optional, NUMBER | The current value of the infinite number (variable $nn). Defaults to 1. |
| `currentMonthlyNumber` | optional, NUMBER | The current value of the monthly number (variable $nm). Defaults to 1. |
| `currentYearlyNumber` | optional, NUMBER | The current value of the yearly number (variable $ny). Defaults to 1. |
| `dailyNumberDigits` | optional, NUMBER | The number of digits for the daily number (variable $nd). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |
| `dayDigits` | optional, NUMBER | The number of digits for the current day (variable $d). Defaults to 2. |
| `infiniteNumberDigits` | optional, NUMBER | The number of digits for the infinite number (variable $nn). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |
| `isSkipExisting` | optional, BOOLEAN | Automatically skip existing sequence numbers? Example: If the next number is 500, but 500 already exists, it will increment the sequence number until a free one is found (max. 100 tries). Possible values: true, false. |
| `monthDigits` | optional, NUMBER | The number of digits for the current month (variable $m). Defaults to 2. |
| `monthlyNumberDigits` | optional, NUMBER | The number of digits for the monthly number (variable $nm). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |
| `yearDigits` | optional, NUMBER | The number of digits for the current year (variable $y). Defaults to 4. |
| `yearlyNumberDigits` | optional, NUMBER | The number of digits for the yearly number (variable $ny). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |

#### Endpoint

```
POST /api/v1/sequencenumber/create.json
```

### Update sequence number

Updates an existing sequence number. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the sequence number to update. |
| `name` | mandatory, TEXT, MAX:100 | A name to describe and identify the sequence number.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: `<values><de>German text</de><en>English text</en></values>` |
| `pattern` | mandatory, TEXT, MAX:50 | The sequence number pattern, which consists of variables and arbitrary text from which a sequence number will be generated. Possible variables: $y = Current year. $m = Current month. $d = Current day. $ny = Sequence number, resets annually (on Jan 1st). $nm = Sequence number, resets monthly. $nd = Sequence number, resets daily. $nn = Sequence number, never resets. Example pattern: `RE-$y$m$d$nd` which may generate 'RE-2007151' (on July 15, 2020). |
| `currentDailyNumber` | optional, NUMBER | The current value of the daily number (variable $nd). Defaults to 1. |
| `currentInfiniteNumber` | optional, NUMBER | The current value of the infinite number (variable $nn). Defaults to 1. |
| `currentMonthlyNumber` | optional, NUMBER | The current value of the monthly number (variable $nm). Defaults to 1. |
| `currentYearlyNumber` | optional, NUMBER | The current value of the yearly number (variable $ny). Defaults to 1. |
| `dailyNumberDigits` | optional, NUMBER | The number of digits for the daily number (variable $nd). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |
| `dayDigits` | optional, NUMBER | The number of digits for the current day (variable $d). Defaults to 2. |
| `infiniteNumberDigits` | optional, NUMBER | The number of digits for the infinite number (variable $nn). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |
| `isSkipExisting` | optional, BOOLEAN | Automatically skip existing sequence numbers? Example: If the next number is 500, but 500 already exists, it will increment the sequence number until a free one is found (max. 100 tries). Possible values: true, false. |
| `monthDigits` | optional, NUMBER | The number of digits for the current month (variable $m). Defaults to 2. |
| `monthlyNumberDigits` | optional, NUMBER | The number of digits for the monthly number (variable $nm). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |
| `yearDigits` | optional, NUMBER | The number of digits for the current year (variable $y). Defaults to 4. |
| `yearlyNumberDigits` | optional, NUMBER | The number of digits for the yearly number (variable $ny). If the number of digits are lower than this, the number will be prepended by zeroes (e.g. 0001 if 4 digits). Defaults to 1. |

#### Endpoint

```
POST /api/v1/sequencenumber/update.json
```

### Delete sequence number

Deletes one or multiple sequence numbers. Only unused sequence numbers can be deleted. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/sequencenumber/delete.json
```

## Tax code

The following API endpoints are for managing tax codes. Tax codes are used e.g. in order items or in journal entries directly. They can also be pre-configured in accounts so they will be automatically used with the corresponding account.

### Read tax code

Returns a single tax code by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/tax/read.json
```

### List tax codes

Returns a list of all tax codes.

#### Endpoint

```
GET /api/v1/tax/list.json
```

### Create tax code

Creates a new tax code. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>code</code></th><td>mandatory, TEXT, MAX:32</td><td>A short code to identify the tax code.</td></tr>
<tr><th><code>components</code></th><td>mandatory, TEXT</td><td>The components of the tax code, up to two possible.
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>ID of the account where the tax amounts are being collected. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>applyRule</code></th><td>mandatory, TEXT</td><td>The application rule, on which account (debit or credit side) the tax is applied. Possible values: CREDIT, DEBIT, REVENUE, EXPENSE, LEGACY_REV, LEGACY_EXP.</td></tr>
<tr><th><code>calcType</code></th><td>mandatory, TEXT</td><td>The calculation basis, how the tax is calculated (either based on the net amount or gross amount). Possible values: NET, GROSS.</td></tr>
<tr><th><code>code</code></th><td>optional, TEXT</td><td>One or multiple codes, comma-separated, corresponding to the code on the tax return form from the ESTV. Example: 200,303</td></tr>
</table>
</td></tr>
<tr><th><code>rates</code></th><td>mandatory, TEXT</td><td>Tax rates that are valid from a given date. Add a new tax rate here if the official tax rate changes. Exactly one tax rate must exist without a valid from date.
<table>
<tr><th><code>percentage</code></th><td>mandatory, NUMBER</td><td>The tax rate percentage (e.g. 8.1).</td></tr>
<tr><th><code>dateValid</code></th><td>optional, DATE</td><td>The date from which the tax rate will be used. One of the tax rates must have no <code>dateValid</code> set, that is the fallback tax rate.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>percentageFlat</code></th><td>optional, NUMBER</td><td>The net/flat tax rate percentage (e.g. 5.9), if net or flat tax rate method is used, otherwise leave empty.</td></tr>
</table>
</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:100</td><td>A description for the tax code.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>documentName</code></th><td>optional, TEXT, MAX:50</td><td>The name for the tax code displayed on documents (seen by customers). If <code>isDisplayTaxRate</code> is set, this name doesn't have to include the tax rate percentage, it will be automatically appended.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>isDisplayTaxRate</code></th><td>optional, BOOLEAN</td><td>Whether to automatically append the current tax rate to the document name (see <code>documentName</code>) or not. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the tax code as inactive. This means that the tax code is greyed out and no longer suggested. Tax codes already in use cannot be deleted, but you can always set them as inactive. Defaults to false. Possible values: true, false.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/tax/create.json
```

### Update tax code

Updates an existing tax code. If a tax code is already being used, only some fields can be changed, but e.g. not the components or an already used tax rate. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

<table>
<tr><th><code>code</code></th><td>mandatory, TEXT, MAX:32</td><td>A short code to identify the tax code.</td></tr>
<tr><th><code>components</code></th><td>mandatory, TEXT</td><td>The components of the tax code, up to two possible.
<table>
<tr><th><code>accountId</code></th><td>mandatory, NUMBER</td><td>ID of the account where the tax amounts are being collected. See <a href="https://app.cashctrl.com/static/help/en/api/index.html#/account">Account</a>.</td></tr>
<tr><th><code>applyRule</code></th><td>mandatory, TEXT</td><td>The application rule, on which account (debit or credit side) the tax is applied. Possible values: CREDIT, DEBIT, REVENUE, EXPENSE, LEGACY_REV, LEGACY_EXP.</td></tr>
<tr><th><code>calcType</code></th><td>mandatory, TEXT</td><td>The calculation basis, how the tax is calculated (either based on the net amount or gross amount). Possible values: NET, GROSS.</td></tr>
<tr><th><code>code</code></th><td>optional, TEXT</td><td>One or multiple codes, comma-separated, corresponding to the code on the tax return form from the ESTV. Example: 200,303</td></tr>
</table>
</td></tr>
<tr><th><code>id</code></th><td>mandatory, NUMBER</td><td>The ID of the tax code to update.</td></tr>
<tr><th><code>rates</code></th><td>mandatory, TEXT</td><td>Tax rates that are valid from a given date. Add a new tax rate here if the official tax rate changes. Exactly one tax rate must exist without a valid from date.
<table>
<tr><th><code>percentage</code></th><td>mandatory, NUMBER</td><td>The tax rate percentage (e.g. 8.1).</td></tr>
<tr><th><code>dateValid</code></th><td>optional, DATE</td><td>The date from which the tax rate will be used. One of the tax rates must have no <code>dateValid</code> set, that is the fallback tax rate.<br>Format: YYYY-MM-DD. Example: <code>2020-01-15</code>.</td></tr>
<tr><th><code>percentageFlat</code></th><td>optional, NUMBER</td><td>The net/flat tax rate percentage (e.g. 5.9), if net or flat tax rate method is used, otherwise leave empty.</td></tr>
</table>
</td></tr>
<tr><th><code>description</code></th><td>optional, TEXT, MAX:100</td><td>A description for the tax code.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>documentName</code></th><td>optional, TEXT, MAX:50</td><td>The name for the tax code displayed on documents (seen by customers). If <code>isDisplayTaxRate</code> is set, this name doesn't have to include the tax rate percentage, it will be automatically appended.<br>This can contain localized text. To add values in multiple languages, use the XML format like this: <code>&lt;values&gt;&lt;de&gt;German text&lt;/de&gt;&lt;en&gt;English text&lt;/en&gt;&lt;/values&gt;</code></td></tr>
<tr><th><code>isDisplayTaxRate</code></th><td>optional, BOOLEAN</td><td>Whether to automatically append the current tax rate to the document name (see <code>documentName</code>) or not. Possible values: true, false.</td></tr>
<tr><th><code>isInactive</code></th><td>optional, BOOLEAN</td><td>Mark the tax code as inactive. This means that the tax code is greyed out and no longer suggested. Tax codes already in use cannot be deleted, but you can always set them as inactive. Defaults to false. Possible values: true, false.</td></tr>
</table>

#### Endpoint

```
POST /api/v1/tax/update.json
```

### Delete tax code

Deletes one or multiple tax codes. Note that you cannot delete tax codes that are being used. Instead use [Update tax code](https://app.cashctrl.com/static/help/en/api/index.html#/tax/update.json) to deactivate the tax code. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/tax/delete.json
```

## Text template

The following API endpoints are for managing text templates. These are used e.g. for the text on the order document (text above / below the items table on the PDF).

### Read text template

Returns a single text template by ID.

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the entry. |

#### Endpoint

```
GET /api/v1/text/read.json
```

### List text templates

Returns a list of text templates by type.

#### Parameters

| | | |
| --- | --- | --- |
| `type` | mandatory, TEXT | The type of text template, meaning: Where the text template can be used. Possible values: ORDER_HEADER, ORDER_FOOTER, ORDER_MAIL, ORDER_ITEM, SALARY_HEADER, SALARY_FOOTER, SALARY_MAIL, SALARY_CERTIFICATE_MAIL. |

#### Endpoint

```
GET /api/v1/text/list.json
```

### Create text template

Creates a new text template. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `name` | mandatory, TEXT, MAX:200 | A name to describe and identify the text template. |
| `type` | mandatory, TEXT | The type of text template, meaning: Where the text template can be used. Possible values: ORDER_HEADER, ORDER_FOOTER, ORDER_MAIL, ORDER_ITEM, SALARY_HEADER, SALARY_FOOTER, SALARY_MAIL, SALARY_CERTIFICATE_MAIL. |
| `isDefault` | optional, BOOLEAN | Sets the text template as the default text template. Note that text templates defined in order categories are preferred over the default text template, see [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category). Defaults to false. Possible values: true, false. |
| `value` | optional, TEXT | The actual text template.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |

#### Endpoint

```
POST /api/v1/text/create.json
```

### Update text template

Updates an existing text template. Note that all parameters must be submitted, omitted parameters are treated as empty values. Returns either a success or multiple error messages (for each issue).

#### Parameters

| | | |
| --- | --- | --- |
| `id` | mandatory, NUMBER | The ID of the text template to update. |
| `name` | mandatory, TEXT, MAX:200 | A name to describe and identify the text template. |
| `type` | mandatory, TEXT | The type of text template, meaning: Where the text template can be used. Possible values: ORDER_HEADER, ORDER_FOOTER, ORDER_MAIL, ORDER_ITEM, SALARY_HEADER, SALARY_FOOTER, SALARY_MAIL, SALARY_CERTIFICATE_MAIL. |
| `isDefault` | optional, BOOLEAN | Sets the text template as the default text template. Note that text templates defined in order categories are preferred over the default text template, see [Order category](https://app.cashctrl.com/static/help/en/api/index.html#/order/category). Defaults to false. Possible values: true, false. |
| `value` | optional, TEXT | The actual text template.<br>This can contain limited HTML for styling. Allowed tags: a, p, div, h1, h2, h3, h4, h5, h6, ul, ol, li, blockquote, b, i, s, u, o, sup, sub, ins, del, strong, strike, tt, code, big, small, br, span, em. Allowed inline CSS rules: background, background-color, color, font, font-size, font-weight, font-style, text-align, text-indent, text-decoration. |

#### Endpoint

```
POST /api/v1/text/update.json
```

### Delete text template

Deletes one or multiple text templates. Returns either a success or error message.

#### Parameters

| | | |
| --- | --- | --- |
| `ids` | mandatory, CSV | The IDs of the selected entries, comma-separated. |

#### Endpoint

```
POST /api/v1/text/delete.json
```
