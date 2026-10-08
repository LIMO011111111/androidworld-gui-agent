"""The rules that live in code. These tests are the evidence for what they stop.

Many cases below come from an adversarial review that tried to get a payment
action past the guard with model output alone.
"""

import pytest

from gui_agent import actions
from gui_agent import config as config_lib
from gui_agent import guardrails
from gui_agent import observation
from tests import fakes

MARKOR = "net.gsantner.markor"
LAUNCHER = "com.google.android.apps.nexuslauncher"


def _resolve(raw, elements, grounding="index"):
  views = observation.build_views(elements, fakes.SCREEN)
  action = actions.parse_action(raw, grounding)
  return actions.resolve_action(action, views, fakes.SCREEN, grounding), views


def _allowed(raw, elements, grounding="index", package=MARKOR, recent=()):
  resolved, views = _resolve(raw, elements, grounding)
  return guardrails.PaymentGuard().check(resolved, views, package, recent).allowed


def _click(index):
  return '{"action_type": "click", "index": %d}' % index


def _button(label="", box=(100, 1000, 980, 1120), **kwargs):
  kwargs.setdefault("cls", "android.widget.Button")
  kwargs.setdefault("clickable", True)
  return fakes.el(label, box, **kwargs)


def _field(hint="", box=(100, 400, 980, 520), **kwargs):
  return fakes.el("", box, hint=hint, cls="android.widget.EditText", editable=True, **kwargs)


PRODUCT_PAGE = [
    fakes.el("Wireless headphones", (0, 200, 1080, 300)),
    _button("Buy now", (100, 1000, 980, 1120)),
    _button("Add to cart", (100, 1200, 980, 1320)),
    _button("Reviews", (100, 1500, 980, 1620)),
    _field("Search", (100, 1800, 980, 1920)),
]
EDITOR = [
    _field("Note text", (0, 300, 1080, 1800)),
    _button("Save", (900, 100, 1050, 200)),
]


# --- payment buttons and links -----------------------------------------------


@pytest.mark.parametrize("index", [1, 2])
def test_payment_buttons_cannot_be_tapped_by_index(index):
  resolved, views = _resolve(_click(index), PRODUCT_PAGE)
  verdict = guardrails.PaymentGuard().check(resolved, views, MARKOR)
  assert not verdict.allowed and verdict.rule == "payment_ban"


def test_payment_buttons_cannot_be_tapped_by_coordinate_either():
  # (500, 440) on the 0-1000 grid is inside the "Buy now" button.
  resolved, views = _resolve('{"action_type": "click", "x": 500, "y": 440}', PRODUCT_PAGE, "coordinate")
  assert resolved.target.text == "Buy now"
  assert not guardrails.PaymentGuard().check(resolved, views, MARKOR).allowed


def test_long_press_and_typing_on_a_payment_button_are_blocked_too():
  assert not _allowed('{"action_type": "long_press", "index": 1}', PRODUCT_PAGE)
  assert not _allowed('{"action_type": "input_text", "index": 1, "text": "x"}', PRODUCT_PAGE)


def test_harmless_controls_on_the_same_screen_stay_usable():
  assert _allowed(_click(3), PRODUCT_PAGE)  # Reviews
  assert _allowed('{"action_type": "input_text", "index": 4, "text": "headphones"}', PRODUCT_PAGE)
  assert _allowed('{"action_type": "scroll", "direction": "down"}', PRODUCT_PAGE)


@pytest.mark.parametrize(
    "label",
    [
        "PAY", "Pay $12.99", "Pay12.99", "PayNow", "BuyNow", "Pay_now", "Buy now",
        "Jetzt zahlen", "Kostenpflichtig buchen", "Complete purchase", "Purchases",
        "Get Premium", "Start free trial", "Add funds", "Subscribe", "Donate",
        "Play Store", "Google Wallet",
        "P a y", "Pa​y now",  # spaced out, zero-width space
        "Рay now",  # Cyrillic capital Er instead of P
        "Buy now with 1-Click and get free delivery tomorrow if you order today",
    ],
)
def test_payment_labels_are_recognised_in_many_spellings(label):
  assert not _allowed(_click(0), [_button(label)])


def test_a_button_with_a_money_amount_is_a_payment_button():
  for label in ("$4.99", "9,99 €", "EUR 12", "Send €20", "Tip $5"):
    assert not _allowed(_click(0), [_button(label)]), label
  # The same text as plain content (an expense row) is not a button.
  assert _allowed(_click(0), [fakes.el("$4.99", (100, 1000, 980, 1120), clickable=True)])


@pytest.mark.parametrize(
    "resource",
    ["com.shop:id/btn_pay", "com.shop:id/payButton", "com.shop:id/btnBuy",
     "com.shop:id/buy_now_button", "com.shop:id/checkoutBtn", "com.shop:id/purchaseButton"],
)
def test_icon_buttons_are_recognised_by_their_resource_id(resource):
  icon = _button("", res=resource, cls="android.widget.ImageButton")
  assert not _allowed(_click(0), [icon])


def test_content_description_alone_is_enough():
  icon = _button("", desc="Pay now button. Double tap to complete your purchase of 3 items")
  assert not _allowed(_click(0), [icon])


@pytest.mark.parametrize("label", ["Display", "Payload editor", "Repay schedule", "Reorder list", "Storage", "Save", "Send", "OK"])
def test_ordinary_labels_are_not_payment_labels(label):
  assert _allowed(_click(0), [_button(label)])


# --- the tree lists leaves only: padding, icons and prices inside a button ----

ROW = [
    # A clickable row whose only listed children are an icon, a label, a price.
    fakes.el("", (60, 1010, 160, 1110), desc="Cart icon", cls="android.widget.ImageView"),
    fakes.el("Pay now", (420, 1030, 660, 1090)),
    fakes.el("$9.99 / month", (760, 1030, 1000, 1090)),
    _button("Help", (100, 1500, 980, 1620)),
]


def test_tap_on_button_padding_next_to_the_label_is_blocked():
  # x=200/1000 is left of the label, inside the row but on no listed element.
  resolved, views = _resolve('{"action_type": "click", "x": 280, "y": 442}', ROW, "coordinate")
  assert resolved.target is None
  assert not guardrails.PaymentGuard().check(resolved, views, MARKOR).allowed


def test_tap_on_the_icon_or_price_inside_a_payment_row_is_blocked():
  assert not _allowed(_click(0), ROW)  # the cart icon
  assert not _allowed(_click(2), ROW)  # the price next to the label
  assert _allowed(_click(3), ROW)  # a different row


# --- payment forms ------------------------------------------------------------

CHECKOUT = [
    fakes.el("Almost done", (0, 200, 1080, 300)),
    _field("Card no.", (100, 400, 980, 520), focused=True),
    _field("MM/YY", (100, 600, 500, 720)),
    _field("CVC", (580, 600, 980, 720)),
    _button("Continue", (100, 1000, 980, 1120)),
]


@pytest.mark.parametrize(
    "raw",
    [
        '{"action_type": "input_text", "index": 1, "text": "hello"}',
        '{"action_type": "input_text", "text": "123"}',  # into the focused field
        '{"action_type": "keyboard_enter"}',  # would submit the form
        '{"action_type": "click", "index": 4}',  # harmless-looking "Continue"
        '{"action_type": "scroll", "direction": "down"}',
    ],
)
def test_on_a_payment_form_everything_but_leaving_is_blocked(raw):
  assert not _allowed(raw, CHECKOUT)


@pytest.mark.parametrize("raw", ['{"action_type": "navigate_back"}', '{"action_type": "navigate_home"}',
                                 '{"action_type": "wait"}', '{"action_type": "status", "goal_status": "infeasible"}'])
def test_leaving_a_payment_form_is_always_possible(raw):
  assert _allowed(raw, CHECKOUT)


@pytest.mark.parametrize(
    "hint, resource",
    [
        ("Card number", ""), ("Name on card", ""), ("Card no.", ""), ("MM/YY", ""),
        ("", "com.shop:id/card_number"), ("", "com.shop:id/et_card_number"),
        ("", "com.shop:id/credit_card_input"), ("", "com.shop:id/iban_input"),
        ("", "com.shop:id/security_code"), ("", "com.shop:id/card_holder_name"),
        ("", "com.shop:id/cardNumber"), ("IBAN", ""), ("Kartennummer", ""),
    ],
)
def test_payment_fields_are_recognised_by_hint_or_id(hint, resource):
  field = _field(hint, res=resource)
  assert not _allowed('{"action_type": "input_text", "index": 0, "text": "12345"}', [field])
  assert not _allowed(_click(0), [field])


def test_enter_and_untargeted_typing_are_blocked_next_to_a_single_pay_button():
  screen = [fakes.el("Your basket", (0, 200, 1080, 300)), _button("Pay €10")]
  assert not _allowed('{"action_type": "keyboard_enter"}', screen)
  assert not _allowed('{"action_type": "input_text", "text": "123"}', screen)


def test_what_the_user_typed_never_turns_a_screen_into_a_payment_form():
  editor = [
      fakes.el("Remember to buy now, pay the checkout fee and note my card number",
               (0, 300, 1080, 1800), hint="Note text", cls="android.widget.EditText", editable=True),
      fakes.el("billing", (0, 1850, 1080, 1950), hint="Title", cls="android.widget.EditText", editable=True),
      _button("Save", (900, 100, 1050, 200)),
  ]
  for raw in (_click(0), _click(1), _click(2), '{"action_type": "keyboard_enter"}',
              '{"action_type": "input_text", "index": 0, "text": "more text"}'):
    assert _allowed(raw, editor), raw


# --- payment data in typed text ------------------------------------------------


def _type(text, recent=()):
  action = actions.AgentAction(action_type="input_text", index=0, text=text)
  views = observation.build_views(EDITOR, fakes.SCREEN)
  resolved = actions.resolve_action(action, views, fakes.SCREEN, "index")
  return guardrails.PaymentGuard().check(resolved, views, MARKOR, recent).allowed


@pytest.mark.parametrize(
    "text",
    [
        "4111 1111 1111 1111", "5500005555555559", "4111-1111-1111-1111",
        "4111.1111.1111.1111", "4111/1111/1111/1111", "4111  1111  1111  1111",
        "4111–1111–1111–1111",  # en dashes: the device drops them
        "4111​1111​1111​1111",  # zero-width spaces
        "4111 1111 1111 1111",  # no-break spaces
        "④①①① 1111 1111 1111",  # circled digits 4111
        "my card is 4111 1111 1111 1111 thanks",
    ],
)
def test_card_numbers_cannot_be_typed_in_any_disguise(text):
  assert not _type(text)


def test_a_card_number_split_over_several_inputs_is_caught():
  assert _type("4111 1111")
  assert not _type("1111 1111", recent=("some note", "4111 1111"))
  assert not _type("1111", recent=("4111", "1111", "1111"))
  # A text in between breaks the run: these are unrelated numbers.
  assert _type("1111 1111", recent=("4111 1111", "see you at 8"))


@pytest.mark.parametrize(
    "text",
    [
        "DE89 3704 0044 0532 0130 00", "DE89370400440532013000",
        "DE89 3704 0044 0532 0130 00 bitte", "DE89370400440532013000 Max Mustermann",
        "DE89-3704-0044-0532-0130-00", "IBAN: GB82 WEST 1234 5698 7654 32",
        "de89 3704 0044 0532 0130 00",
    ],
)
def test_ibans_cannot_be_typed(text):
  assert not _type(text)


@pytest.mark.parametrize(
    "text",
    [
        "+17631706690",  # phone number from a task
        "Don't forget to buy milk and pay the plumber.",
        "friendly_koala_2023_03_02.txt",
        "1234567890123456",  # 16 digits, but not a valid card number
        "Meeting at 10am in room 42B, bring 3 copies of DE12 report",
        "Order 2023-10-15 15:34:00 ref 12345",
        "DE89 3704 0044 0532 0130 01",  # wrong checksum: not an IBAN
    ],
)
def test_ordinary_text_is_not_mistaken_for_payment_data(text):
  assert _type(text)


def test_task_texts_from_androidworld_trigger_no_rule():
  pytest.importorskip("android_world")
  from android_world.task_evals.utils import user_data_generation as generation

  samples = list(generation.RANDOM_SENTENCES)
  samples += [generation.generate_random_name() for _ in range(300)]
  samples += [generation.generate_random_number() for _ in range(300)]
  samples += [generation.generate_random_file_name() + ".md" for _ in range(300)]
  for text in samples:
    assert _type(text), text
    row = [fakes.el(text, (0, 400, 1080, 520), clickable=True)]
    assert _allowed(_click(0), row), text


# --- payment apps --------------------------------------------------------------


def test_nothing_but_leaving_is_allowed_while_a_payment_app_is_visible():
  # Three store elements, outnumbered by ten elements of another window.
  screen = [_button("$4.99", (100, 300 + 60 * i, 400, 350 + 60 * i), package="com.android.vending") for i in range(3)]
  screen += [fakes.el(f"row {i}", (500, 300 + 60 * i, 900, 350 + 60 * i), clickable=True) for i in range(10)]
  assert not _allowed(_click(5), screen, package=MARKOR)  # even a harmless row
  assert not _allowed('{"action_type": "keyboard_enter"}', screen, package=MARKOR)
  assert _allowed('{"action_type": "navigate_home"}', screen, package="com.android.vending")


@pytest.mark.parametrize("name", ["Play Store", "Google Pay", "PayPal", "amazon shopping", "wallet",
                                  "com.android.vending", "com.paypal.android.p2pmobile", "My Bank"])
def test_payment_apps_cannot_be_opened(name):
  assert not _allowed('{"action_type": "open_app", "app_name": "%s"}' % name, PRODUCT_PAGE)


def test_no_allowed_app_is_a_payment_app():
  for name, package in config_lib.APP_PACKAGES.items():
    assert _allowed('{"action_type": "open_app", "app_name": "%s"}' % name, EDITOR), name
    assert not guardrails.is_payment_package(package), package


def test_allowed_app_packages_match_androidworlds_launch_table():
  pytest.importorskip("android_world")
  from android_world.env import adb_utils

  for name, package in config_lib.APP_PACKAGES.items():
    activity = adb_utils.get_adb_activity(name)
    assert activity is not None and activity.split("/")[0] == package, name


# --- app scope: the structural layer --------------------------------------------


def _scope(raw, package, elements=EDITOR, grounding="index"):
  resolved, _ = _resolve(raw, elements, grounding)
  scope = guardrails.AppScope(config_lib.AgentConfig().scope_packages())
  return scope.check(resolved, package)


ACTING = [
    _click(1),
    '{"action_type": "long_press", "index": 1}',
    '{"action_type": "input_text", "index": 0, "text": "x"}',
    '{"action_type": "input_text", "text": "x"}',
    '{"action_type": "keyboard_enter"}',
    '{"action_type": "scroll", "direction": "down"}',
]
LEAVING = [
    '{"action_type": "navigate_back"}', '{"action_type": "navigate_home"}',
    '{"action_type": "wait"}', '{"action_type": "open_app", "app_name": "markor"}',
    '{"action_type": "status", "goal_status": "complete"}',
]


@pytest.mark.parametrize("package", ["com.android.chrome", "com.android.vending", "com.unknown.shop",
                                     "com.google.android.gms", "com.google.android.googlequicksearchbox"])
def test_outside_the_allowed_apps_the_agent_can_only_leave(package):
  for raw in ACTING:
    verdict = _scope(raw, package)
    assert not verdict.allowed and verdict.rule == "app_scope", raw
  for raw in LEAVING:
    assert _scope(raw, package).allowed, raw


@pytest.mark.parametrize("package", [MARKOR, "com.simplemobiletools.smsmessenger",
                                     "com.google.android.contacts", "android",
                                     "com.google.android.permissioncontroller"])
def test_inside_the_allowed_apps_and_system_dialogs_it_can_act(package):
  for raw in ACTING + LEAVING:
    assert _scope(raw, package).allowed, raw


def test_home_screen_icons_cannot_be_tapped_apps_are_opened_by_name():
  home = [fakes.el("", (100, 2000, 300, 2200), desc="Play Store", clickable=True, package=LAUNCHER),
          fakes.el("", (400, 2000, 600, 2200), desc="Markor", clickable=True, package=LAUNCHER)]
  for raw in (_click(0), _click(1), '{"action_type": "long_press", "index": 1}',
              '{"action_type": "input_text", "index": 1, "text": "markor"}'):
    verdict = _scope(raw, LAUNCHER, home)
    assert not verdict.allowed and verdict.rule == "home_screen", raw
  assert not _scope('{"action_type": "click", "x": 500, "y": 875}', LAUNCHER, home, "coordinate").allowed
  assert _scope('{"action_type": "open_app", "app_name": "markor"}', LAUNCHER, home).allowed
  # And the store icon is a payment label in its own right.
  assert not _allowed(_click(0), home, package=LAUNCHER)


def test_unknown_foreground_app_means_no_acting():
  for raw in ACTING:
    assert not _scope(raw, "").allowed
  assert _scope('{"action_type": "wait"}', "").allowed


def test_payment_apps_cannot_be_configured_into_scope():
  with pytest.raises(ValueError, match="payment apps"):
    guardrails.AppScope(("net.gsantner.markor", "com.android.vending"))
  with pytest.raises(ValueError, match="browsers"):
    guardrails.AppScope(("net.gsantner.markor", "com.android.chrome"))
  with pytest.raises(ValueError, match="payment apps"):
    cfg = config_lib.AgentConfig(extra_scope_packages=("com.paypal.android.p2pmobile",))
    guardrails.AppScope(cfg.scope_packages())
  with pytest.raises(ValueError, match="not in APP_PACKAGES"):
    config_lib.AgentConfig(allowed_apps=("markor", "com.android.vending"))
  with pytest.raises(ValueError, match="not in APP_PACKAGES"):
    config_lib.AgentConfig(allowed_apps=("chrome",))


# --- app allow-list --------------------------------------------------------------


def test_allow_list_blocks_unknown_apps_and_names_the_valid_ones():
  allow = guardrails.AppAllowList(("markor", "simple sms messenger"))
  resolved, _ = _resolve('{"action_type": "open_app", "app_name": "Messages"}', EDITOR)
  verdict = allow.check(resolved)
  assert not verdict.allowed and verdict.rule == "app_allow_list"
  assert "simple sms messenger" in verdict.message


@pytest.mark.parametrize("name", ["com.android.vending", "markor ; rm", "mark.*", "Markor​", "sms"])
def test_allow_list_does_not_fall_for_odd_names(name):
  allow = guardrails.AppAllowList(config_lib.DEFAULT_ALLOWED_APPS)
  resolved, _ = _resolve('{"action_type": "open_app", "app_name": "%s"}' % name, EDITOR)
  assert not allow.check(resolved).allowed


def test_allow_list_rewrites_near_miss_names_to_the_exact_one():
  allow = guardrails.AppAllowList(("markor", "simple sms messenger"))
  resolved, _ = _resolve('{"action_type": "open_app", "app_name": "Simple SMS"}', EDITOR)
  assert allow.check(resolved).allowed
  assert resolved.env_action["app_name"] == "simple sms messenger"
  resolved, _ = _resolve('{"action_type": "open_app", "app_name": "  MARKOR "}', EDITOR)
  assert allow.check(resolved).allowed
  assert resolved.env_action["app_name"] == "markor"


# --- step budget -------------------------------------------------------------------


def test_task_budget_can_lower_but_never_raise_the_hard_limit():
  budget = guardrails.StepBudget(20)
  budget.set_task_budget(12)
  assert budget.budget == 12
  budget.set_task_budget(600)
  assert budget.budget == 20
  budget.set_task_budget(-5)
  assert budget.budget == 1


def test_budget_is_exhausted_after_exactly_n_steps():
  budget = guardrails.StepBudget(3)
  for expected in (1, 2, 3):
    assert not budget.exhausted()
    assert budget.consume() == expected
  assert budget.exhausted()


# --- loop detection ------------------------------------------------------------------


def test_same_action_on_same_screen_is_blocked_on_the_third_try():
  loop = guardrails.LoopDetector()
  assert loop.check("tap-5", "screen-a").allowed
  assert loop.check("tap-5", "screen-a").allowed
  verdict = loop.check("tap-5", "screen-a")
  assert not verdict.allowed and verdict.rule == "loop_guard"
  assert loop.blocks == 1


def test_progress_resets_the_loop_counter():
  loop = guardrails.LoopDetector()
  # Typing "1" twice on a keypad: same action, but the screen changes.
  assert loop.check("tap-1", "display-empty").allowed
  assert loop.check("tap-1", "display-1").allowed
  assert loop.check("tap-1", "display-11").allowed
  assert loop.check("tap-2", "display-111").allowed
  assert loop.blocks == 0
