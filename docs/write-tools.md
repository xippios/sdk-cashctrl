# Write tools

How a write tool of this package is built and tested. `src/xippios/cashctrl/tasks_write.py`
holds fourteen write tasks, served by `xippios-cashctrl-mcp-write` alone. The rules they keep
stand in `CLAUDE.md` under Write tools, the decisions taken for them in the docstring of
`tasks_write.py`, and what upstream was seen doing on a write in `docs/upstream/OBSERVED.md`,
under Writes. This document walks one more write through its two layers, its docstring and
its tests.

## The endpoint wrapper

`api/<module>_create.py`, and `_update` and `_delete` beside it, hold a `<module>_fields`
builder and the wrapper. The builder takes every parameter the create table documents,
snake_cased, and returns the form fields under upstream's names through `api/_form.py`'s
`form_fields`, which encodes them as its docstring says: booleans as `true` and `false`, a
`Decimal` as plain digits, dates as `YYYY-MM-DD`, lists as compact JSON with upstream's keys,
`None` and empty lists left out. The wrapper takes `org` and those fields and posts them with
`post_form`, core's `data=` with `charset=UTF-8` declared, and returns a `WriteAnswer`. A
`delete.json` takes `delete_fields(ids)`. The items of a JSON array are `*Input` models in
`models.py`, with `validation_alias=AliasChoices(snake, camel)` and
`serialization_alias=camel`, and they refuse an unknown key.

## The task

An async task in `tasks_write.py` takes `org` first and `confirm: bool = False` last, and the
create table's parameters as keyword arguments between them,
`custom: Mapping[str, str] | None` among them. Over MCP the tool's schema turns `"true"`,
`"yes"`, `"1"` and `1` into `True` and refuses what is no boolean. The task returns
`Result[WritePreview[<record>] | WriteResult]`:

- while `confirm` is false, a `WritePreview`: `performed=False`, `endpoint`, `payload` (the
  exact fields), `before` (for an update or a delete, the record as the read task's
  projection shows it) and `changes` (for an update), with `meta.request` `{"org": org}`;
- with `confirm`, a `WriteResult`: `performed=True`, `insert_id` and `message`, with
  `meta.request` holding `org` and the fields as sent.

`_shown` writes `REDACTED` for `ssn` and an `iban` in what a result shows, and a cleared `ssn`
as empty.

## An update

Upstream empties every parameter an update leaves out, so an `update.json` task reads the
record, maps every parameter the update table documents from it (`_journal_values`,
`_person_values`, `_order_values`, `_book_entry_values`), applies the arguments given (those
not `None`) and sends all of them. An order's items go back under the keys the items table
documents (`_order_items`, in their `pos`), the computed ones left out; upstream stores the
items an update sends anew, with new ids. `person/read.json` returns every stored documented
field and leaves the empty ones out.

Before any write, the task refuses with `InvalidRequestError`, unless the call gives or clears
what is missing:

- a mandatory parameter that neither the record nor the call gives;
- a stored list whose shape was never observed: attachments, allocations, bank accounts,
  children, service periods, insurance contracts, certificate values, an order item's
  allocations;
- a stored key the input table does not document: an address's `titleId`, a contact's
  `purpose`, an order item's `attachments` or `isOptional`;
- a field whose absence from the read is unknown rather than empty: an insurance's
  `insuranceNr` and `insuranceMemberNr`, an employee's `userId`.

`clear: list[str] | None` names the parameters to send empty, a flag (`_FLAGS`) as `false`,
checked against the documented update parameters of the resource (`JOURNAL_UPDATE`,
`PERSON_UPDATE`, `ORDER_UPDATE`, `BOOK_ENTRY_UPDATE`). A parameter both given and cleared is
refused, and so is one that an update sends only when it is given (`_UNSENT`:
`sequence_number_id`). An order is not refused for being booked, since upstream changes an
order's automatic book entries through its items (`docs/upstream/order.md`, Book entry): the
entries its items book are `GENERATED`, and an entry booked by hand is `MANUAL`.

## Custom fields

`custom` maps `customField<ID>` (`api/_form.py`'s `CUSTOM_FIELD`) to text, rendered as
`<values><customField1>...</customField1></values>`, every value escaped. An update merges the
values given into the stored XML (`merge_custom`).

## The docstring

A write task's docstring is its tool's description, so it says what an agent needs to call
the tool right:

- a journal `amount` with a `tax_id` is gross, VAT included, and an order item's `unitPrice`
  was read as gross;
- a preview is free, and `confirm=true` writes;
- the ids come from `list_accounts`, `list_tax_codes`, `list_persons`,
  `list_order_categories`, `list_currencies` and the discovery lists:
  `list_person_categories` (a person's `category_id`), `list_person_titles` (`title_id`),
  `list_locations` (an employee's `location_id`), `list_account_categories` (the
  `category_id` that narrows `list_accounts`), `list_cost_centers` (an allocation's
  `to_cost_center_id`) and `list_custom_fields` (`customField<id>`, by the module's `type`);
- upstream refuses with HTTP 200 and an `errors` list (`RequestRejected` naming the fields),
  and a delete of an id that no longer exists answers `success: false` with `message`
  (`RequestRejected`, not `NotFoundError`);
- `person.nr` is unique: a second person with the same `nr` is refused.

## The tests

The task's preview computes the payload offline, and `scripts/record_fixture.py` records
exactly those pairs: the create, the read the update starts from, the update and the delete,
in that order. `tests/test_tasks_write.py` replays them: the preview sends no request, its
`payload` equals the recorded request body, and `confirm=True` sends it. An update's refusal
is tested on a recorded read changed in memory, and the test says so.

`tests/test_live.py` holds one test per resource. Every record it creates carries the marker
`xippios-live` in its title, company or description, and as its `nr` where it has one, so that
no sequence number advances, and is dated 2026-10-24. The test first lists its resource with
`query=xippios-live` and deletes each record whose marked field holds the marker, the
leftovers of an earlier run. An update is previewed, confirmed and read back: the changed
field holds the new value, and every other field the update derives is unchanged.

## Statuses and payments

`update_order_status` and `create_order_payment` send the fields they are given and read
nothing. A payment, a pain.001 file or a PDF, books nothing and has no documented delete, so
the live test that pays an order deletes the order and leaves its payment behind.
