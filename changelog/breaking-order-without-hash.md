- `get_order` and the `before` of an order's write preview leave out `hash`, an undocumented
  text that may be the token of a public link to the order's document and that the fixture
  recorder already treated as one. They return the new `OrderDetailProjection`, every field
  of `OrderDetail` but `hash`. (https://github.com/xippios/sdk-cashctrl/issues/142)
