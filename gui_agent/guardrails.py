"""Guardrails: rules that must hold live in code, not in the prompt.

Lecture Day 5, "Put the fix in": *a rule that must never be bypassed ->
Programs, because a model can be persuaded out of a rule; a code path cannot.*

Every check here runs AFTER the model has decided and BEFORE anything reaches
the device. The model cannot switch any of it off, whatever it outputs.

1. Step limit      - `StepBudget`
2. Payment ban     - two layers:
     `AppScope`      structural: the agent can only act inside a closed set of
                     apps, none of which can pay for anything. In any other
                     app it can only leave. This is what makes the ban hold
                     for screens and labels nobody thought of.
     `PaymentGuard`  deny rules on top: payment apps, payment forms, payment
                     buttons and fields, card numbers and IBANs.
3. App allow-list  - `AppAllowList` for `open_app` (also the `wrong_app` fix)
4. Loop detection  - `LoopDetector` (same action, same screen, no effect)
"""

from __future__ import annotations

import dataclasses
import re
import unicodedata
from typing import Optional, Sequence

from gui_agent import actions
from gui_agent import observation


@dataclasses.dataclass(frozen=True)
class Verdict:
  """Result of a guardrail check."""

  allowed: bool
  rule: str = ""
  message: str = ""  # shown to the model in the history when blocked

  @classmethod
  def ok(cls) -> "Verdict":
    return cls(True)

  @classmethod
  def block(cls, rule: str, message: str) -> "Verdict":
    return cls(False, rule, message)


# Actions that can never do harm: leaving, stopping, doing nothing.
_SAFE_ACTIONS = (
    actions.NAVIGATE_BACK,
    actions.NAVIGATE_HOME,
    actions.STATUS,
    actions.WAIT,
)


# --- 1. Step limit -----------------------------------------------------------


class StepBudget:
  """Hard cap on the number of steps of one episode."""

  def __init__(self, hard_limit: int):
    if hard_limit < 1:
      raise ValueError("hard_limit must be at least 1")
    self._hard_limit = int(hard_limit)
    self._budget = int(hard_limit)
    self.used = 0

  @property
  def budget(self) -> int:
    return self._budget

  def set_task_budget(self, task_budget: int) -> None:
    """A task may lower the budget, never raise it above the hard limit."""
    self._budget = max(1, min(self._hard_limit, int(task_budget)))

  def reset(self) -> None:
    self.used = 0

  def exhausted(self) -> bool:
    return self.used >= self._budget

  def consume(self) -> int:
    """Counts one step and returns its 1-based number."""
    self.used += 1
    return self.used


# --- Text normalisation shared by the payment rules --------------------------

# Letters from other alphabets that look like Latin ones ("Рay" with a
# Cyrillic P). Folded before matching so look-alikes cannot dodge a word list.
_CONFUSABLES = str.maketrans({
    "а": "a", "в": "b", "е": "e", "к": "k", "м": "m", "н": "h", "о": "o",
    "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i", "ј": "j",
    "ѕ": "s", "ԁ": "d", "һ": "h", "А": "A", "В": "B", "Е": "E", "К": "K",
    "М": "M", "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T", "У": "Y",
    "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S", "α": "a", "ο": "o", "ρ": "p",
    "ν": "v", "υ": "u", "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H",
    "Ι": "I", "Κ": "K", "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T",
    "Υ": "Y", "Χ": "X",
})


def normalise_label(text: str) -> str:
  """Canonical form of a UI label for matching against the payment lists.

  "PayNow", "pay_now", "Pay12.99", "Pa​y now" and "Рay now" (Cyrillic)
  all become text in which "pay" is a separate lower-case word.
  """
  text = unicodedata.normalize("NFKC", text or "")
  text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
  text = text.translate(_CONFUSABLES)
  text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)  # camelCase
  text = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", text)
  text = re.sub(r"[_\-./:|]+", " ", text)
  text = " ".join(text.lower().split())
  # "p a y  n o w" -> "pay now": join runs of single letters.
  return re.sub(r"\b((?:\w ){2,}\w)\b", lambda m: m.group(1).replace(" ", ""), text)


def as_device_types(text: str) -> str:
  """The characters the device will actually receive.

  AndroidWorld's `type_text` NFKD-normalises and drops everything that is not
  ASCII. The guard must judge that string, not the one the model wrote:
  "4111–1111–1111–1111" with en dashes arrives as sixteen digits.
  """
  normalised = unicodedata.normalize("NFKD", text or "")
  return normalised.encode("ascii", "ignore").decode("ascii")


# --- 2a. Payment ban, structural layer: app scope -----------------------------

# Apps whose purpose is buying or paying. Matched as prefixes of the package.
PAYMENT_PACKAGES = (
    "com.android.vending",  # Play Store, also hosts the Play billing sheet
    "com.google.android.apps.walletnfcrel",  # Google Wallet
    "com.google.android.apps.nbu.paisa",  # Google Pay
    "com.google.android.finsky",
    "com.paypal",
    "com.amazon",
    "com.ebay",
    "com.venmo",
    "com.squareup",
    "com.klarna",
    "com.eg.android.AlipayGphone",
    "com.grubhub",
    "com.starbucks",
    "com.shopify",
    "com.stripe",
)


# Browsers can reach any web shop, so they can never be put in scope either.
BROWSER_PACKAGES = (
    "com.android.chrome",
    "com.chrome",
    "com.android.browser",
    "org.mozilla",
    "org.chromium",
    "com.brave",
    "com.opera",
    "com.microsoft.emmx",
    "com.duckduckgo",
    "com.google.android.googlequicksearchbox",
)


def is_payment_package(package: str) -> bool:
  return bool(package) and any(package.startswith(p) for p in PAYMENT_PACKAGES)


def is_browser_package(package: str) -> bool:
  return bool(package) and any(package.startswith(p) for p in BROWSER_PACKAGES)


class AppScope:
  """The agent may only act inside a closed set of apps.

  `scope_packages` are the packages of the allowed apps plus Android's own
  surfaces (dialogs, share sheet, permission prompts). When any other app is
  in the foreground the only permitted actions are the ones that leave it.
  None of the allowed apps can pay for anything, so a payment is not
  something the agent can reach, whatever the screen says and whatever the
  model outputs.

  On the home screen the agent may not tap or type at all: apps are opened
  with `open_app` and an exact name, never by hunting for an icon.
  """

  RULE = "app_scope"
  HOME_RULE = "home_screen"  # same layer, logged separately: usually harmless

  def __init__(self, scope_packages: Sequence[str]):
    banned = [
        p for p in scope_packages
        if is_payment_package(p) or is_browser_package(p)
    ]
    if banned:
      raise ValueError(
          f"payment apps and browsers cannot be put in scope: {banned}"
      )
    self._scope = frozenset(scope_packages)

  def check(self, resolved: actions.ResolvedAction, package: str) -> Verdict:
    kind = resolved.action.action_type
    if kind in _SAFE_ACTIONS or kind == actions.OPEN_APP:
      return Verdict.ok()
    if not package:
      return Verdict.block(
          self.RULE,
          "BLOCKED: it is not clear which app is in front. Wait, go back or"
          " use open_app.",
      )
    if observation.is_launcher_package(package):
      if kind in actions.POINTING_ACTIONS:
        return Verdict.block(
            self.HOME_RULE,
            "BLOCKED: do not tap or type on the home screen. Open the app you"
            " need with open_app and its exact name.",
        )
      return Verdict.ok()
    if package in self._scope:
      return Verdict.ok()
    return Verdict.block(
        self.RULE,
        f"BLOCKED: this screen belongs to {package}, which is outside the"
        " apps you may operate. Go back, or use open_app with an allowed app.",
    )


# --- 2b. Payment ban, deny rules ----------------------------------------------

# Words that start, confirm or prepare a payment, matched as whole words on a
# normalised label. English and German.
_PAYMENT_WORDS = (
    r"pay(?: now)?|payment|payments|buy(?: now)?|purchases?|checkout|check out|"
    r"place (?:your )?order|order now|complete order|confirm order|1 click|"
    r"subscribe|subscription|subscriptions|donate|donation|"
    r"add to cart|add to basket|add (?:a )?(?:payment method|card)|"
    r"top up|add funds|send money|transfer money|"
    r"upgrade to pro|go premium|get premium|premium|free trial|"
    r"unlock full version|in app purchase|"
    r"google pay|gpay|paypal|apple pay|klarna|venmo|alipay|cash app|"
    r"play store|google play|wallet|amazon|ebay|"
    r"bezahlen|zahlen|jetzt kaufen|kaufen|kauf abschlie(?:ß|ss)en|"
    r"zahlungspflichtig|kostenpflichtig|bestellen|bestellung abschicken|"
    r"abonnieren|abo|spenden|in den warenkorb|zur kasse|überweisen|geld senden"
)
_PAYMENT_LABEL_RE = re.compile(r"(?<!\w)(?:" + _PAYMENT_WORDS + r")(?!\w)")

# A button with a money amount in its label: "$4.99", "9,99 €", "Send €20".
_PRICE_RE = re.compile(
    r"[$€£¥] ?\d|\d ?[$€£¥]|\d ?(?:eur|usd|gbp)\b|\b(?:eur|usd|gbp) ?\d"
)

# Input fields that collect payment details (hint, id or description).
_PAYMENT_FIELD_RE = re.compile(
    r"card ?(?:number|no|num|holder|owner)\b|name on card|credit ?card|"
    r"debit ?card|\bcvv\b|\bcvc\b|\bcvn\b|security code|expir(?:y|ation)|"
    r"\bexp date\b|\bmm ?yy(?:yy)?\b|\biban\b|\bbic\b|\bswift\b|billing|"
    r"account number|routing number|sort code|"
    r"kartennummer|kreditkarte|prüfnummer|pruefnummer|kontonummer"
)

# Texts that, seen together, mean "this is a checkout / payment screen".
_PAYMENT_SCREEN_SIGNALS = (
    "card number", "cvv", "cvc", "expiration date", "expiry date", "pay now",
    "place order", "place your order", "checkout", "payment method",
    "billing address", "order total", "google pay", "paypal", "kartennummer",
    "jetzt kaufen", "zahlungspflichtig bestellen", "zahlungsmethode",
    "zur kasse",
)

# Names that must never be opened, whatever a config says.
_PAYMENT_APP_NAME_RE = re.compile(
    r"play ?store|google ?play|\bgps\b|wallet|google ?pay|gpay|paypal|amazon|"
    r"amzn|ebay|venmo|cash ?app|klarna|alipay|grubhub|starbucks|bank|shop|"
    r"store|vending|finsky"
)

_MAX_SIGNAL_LABEL = 60  # longer texts are content, not labels
_ROW_BAND_PX = 48  # how far around a payment label a tap is still "on it"

_CARD_RE = re.compile(r"(?<!\d)\d(?:[ \-./_]{0,2}\d){12,18}(?!\d)")
_DIGIT_CHUNK_RE = re.compile(r"^[\d \-./_]+$")

# IBAN length per country. Only the exact length is tested, so ordinary text
# that happens to start with two letters and two digits is not flagged.
_IBAN_LENGTHS = {
    "AT": 20, "BE": 16, "BG": 22, "CH": 21, "CY": 28, "CZ": 24, "DE": 22,
    "DK": 18, "EE": 20, "ES": 24, "FI": 18, "FR": 27, "GB": 22, "GR": 27,
    "HR": 21, "HU": 28, "IE": 22, "IS": 26, "IT": 27, "LI": 21, "LT": 20,
    "LU": 20, "LV": 21, "MC": 27, "MT": 31, "NL": 18, "NO": 15, "PL": 28,
    "PT": 25, "RO": 24, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "TR": 26,
}
_IBAN_RE = re.compile(r"(?<![A-Z0-9])[A-Z]{2}\d{2}(?:[ \-]?[A-Z0-9]){11,30}")


def _luhn_ok(digits: str) -> bool:
  total = 0
  for i, ch in enumerate(reversed(digits)):
    d = int(ch)
    if i % 2 == 1:
      d *= 2
      if d > 9:
        d -= 9
    total += d
  return total % 10 == 0


def looks_like_card_number(text: str) -> bool:
  """True for 13-19 digit numbers that pass the Luhn check (card numbers).

  Judged on the text as the device receives it; separators between the digits
  (spaces, dashes, dots, slashes) do not hide a number.
  """
  for match in _CARD_RE.finditer(as_device_types(text)):
    digits = re.sub(r"\D", "", match.group())
    if 13 <= len(digits) <= 19 and _luhn_ok(digits):
      return True
  return False


def looks_like_iban(text: str) -> bool:
  """True if the text contains an IBAN with a valid mod-97 checksum."""
  upper = as_device_types(text).upper()
  for match in _IBAN_RE.finditer(upper):
    compact = re.sub(r"[ \-]", "", match.group())
    length = _IBAN_LENGTHS.get(compact[:2])
    if not length or len(compact) < length:
      continue
    iban = compact[:length]
    rearranged = iban[4:] + iban[:4]
    if int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1:
      return True
  return False


class PaymentGuard:
  """Deny rules of the payment ban.

  Blocks, in this order:
    a. opening an app that exists to buy or pay,
    b. everything except leaving while such an app is visible,
    c. everything except leaving on a payment form (any payment field on
       screen, or two payment signals),
    d. taps and typing on, or right next to, an element whose label is about
       paying or buying. Every element under the tap point is checked, and so
       is the row around a payment label, because a button's padding and the
       icon or price inside it are separate boxes in the accessibility tree,
    e. typing or pressing Enter without a known target while a payment
       element is on screen,
    f. typing something that is a card number or an IBAN, in one go or in
       consecutive chunks, judged on the text the device will receive.
  """

  RULE = "payment_ban"
  MESSAGE = (
      "BLOCKED by the payment guardrail: payments, purchases and entering"
      " payment details are forbidden. Go back and continue without paying."
  )

  def _block(self) -> Verdict:
    return Verdict.block(self.RULE, self.MESSAGE)

  def check(
      self,
      resolved: actions.ResolvedAction,
      views: Sequence[observation.ElementView],
      package: str = "",
      recent_typed: Sequence[str] = (),
  ) -> Verdict:
    kind = resolved.action.action_type

    if kind == actions.OPEN_APP:  # (a)
      name = normalise_label(resolved.action.app_name or "")
      raw = (resolved.action.app_name or "").lower()
      if _PAYMENT_APP_NAME_RE.search(name) or _PAYMENT_APP_NAME_RE.search(raw):
        return self._block()
      return Verdict.ok()
    if kind in _SAFE_ACTIONS:
      return Verdict.ok()

    if is_payment_package(package) or any(  # (b)
        is_payment_package(v.package) for v in views
    ):
      return self._block()

    payment_elements = [v for v in views if self.is_payment_element(v)]
    if self.is_payment_screen(views):  # (c)
      return self._block()

    if kind in actions.POINTING_ACTIONS and resolved.tap_xy is not None:  # (d)
      x, y = resolved.tap_xy
      under_tap = observation.hits_at(views, x, y)
      if resolved.target is not None:
        under_tap.append(resolved.target)
      if any(self.is_payment_element(v) for v in under_tap):
        return self._block()
      for element in payment_elements:
        if element.y_min - _ROW_BAND_PX <= y <= element.y_max + _ROW_BAND_PX:
          return self._block()

    if payment_elements:  # (e)
      if kind == actions.KEYBOARD_ENTER:
        return self._block()
      if kind == actions.INPUT_TEXT and resolved.tap_xy is None:
        return self._block()

    if kind == actions.INPUT_TEXT:  # (f)
      text = resolved.action.text or ""
      if looks_like_card_number(text) or looks_like_iban(text):
        return self._block()
      if self._chunked_card_number(recent_typed, text):
        return self._block()

    return Verdict.ok()

  @staticmethod
  def is_payment_element(view: observation.ElementView) -> bool:
    """True if the element is a payment field or a pay / buy control."""
    if view.editable:
      # What the user typed into a field is content, not a label, and is
      # never used to classify the field.
      labels = [view.hint, view.resource, view.description]
      return any(_PAYMENT_FIELD_RE.search(normalise_label(l)) for l in labels if l)
    for label in (view.text, view.description, view.resource):
      if not label:
        continue
      normalised = normalise_label(label)
      if _PAYMENT_LABEL_RE.search(normalised):
        return True
      if view.class_name.endswith("Button") and _PRICE_RE.search(normalised):
        return True
    return False

  @classmethod
  def is_payment_screen(cls, views: Sequence[observation.ElementView]) -> bool:
    """A payment field on screen, or two independent payment signals."""
    if any(v.editable and cls.is_payment_element(v) for v in views):
      return True
    # Only labels and short static texts count as signals. Long free text (a
    # note being written, a message body) must not lock a screen.
    texts = []
    for v in views:
      if not v.editable:
        texts.extend(
            t for t in (v.text, v.description) if len(t) <= _MAX_SIGNAL_LABEL
        )
    haystack = " | ".join(normalise_label(t) for t in texts if t)
    hits = {s for s in _PAYMENT_SCREEN_SIGNALS if s in haystack}
    return len(hits) >= 2

  @staticmethod
  def _chunked_card_number(recent_typed: Sequence[str], text: str) -> bool:
    """A card number typed as several digit-only inputs in a row."""
    current = as_device_types(text)
    if not _DIGIT_CHUNK_RE.match(current):
      return False
    digits = re.sub(r"\D", "", current)
    for earlier in reversed(list(recent_typed)):
      chunk = as_device_types(earlier)
      if not _DIGIT_CHUNK_RE.match(chunk):
        break
      digits = re.sub(r"\D", "", chunk) + digits
      if 13 <= len(digits) <= 19 and _luhn_ok(digits):
        return True
    return False


# --- 3. App allow-list -------------------------------------------------------

# Near-miss spellings that are corrected to the exact name. Anything else that
# is not on the list is blocked.
_APP_ALIASES = {
    "simple sms": "simple sms messenger",
    "sms messenger": "simple sms messenger",
    "simple sms messenger app": "simple sms messenger",
    "markor app": "markor",
    "contacts app": "contacts",
    "clock app": "clock",
    "settings app": "settings",
    "system settings": "settings",
    "camera app": "camera",
    "files app": "files",
    "file manager": "files",
    "simple calendar": "simple calendar pro",
    "simple gallery": "simple gallery pro",
    "opentracks": "open tracks",
    "pro expense app": "pro expense",
    "tasks app": "tasks",
    "vlc player": "vlc",
}


class AppAllowList:
  """`open_app` works only for names on the list.

  Fix for the `wrong_app` failure class: a name that would start a different
  app (for example "Messages" instead of "Simple SMS Messenger") never
  reaches the device. A few near-miss spellings are corrected to the exact
  name in code; the correction is visible in the history line.
  """

  RULE = "app_allow_list"

  def __init__(self, allowed_apps: Sequence[str]):
    self.allowed = tuple(a.strip().lower() for a in allowed_apps)
    if not self.allowed:
      raise ValueError("allowed_apps must not be empty")

  def canonical(self, app_name: str) -> Optional[str]:
    name = " ".join((app_name or "").strip().lower().split())
    name = _APP_ALIASES.get(name, name)
    return name if name in self.allowed else None

  def check(self, resolved: actions.ResolvedAction) -> Verdict:
    """Blocks unknown apps; rewrites near-miss names to the exact one."""
    if resolved.action.action_type != actions.OPEN_APP:
      return Verdict.ok()
    canonical = self.canonical(resolved.action.app_name or "")
    if canonical is None:
      return Verdict.block(
          self.RULE,
          f'BLOCKED: "{resolved.action.app_name}" is not an app you may open.'
          f" Use open_app with exactly one of: {', '.join(self.allowed)}.",
      )
    resolved.env_action["app_name"] = canonical
    resolved.description = f"open_app {canonical}"
    return Verdict.ok()


# --- 4. Loop detection -------------------------------------------------------


class LoopDetector:
  """Detects "same action on the same screen, again" (Day 4, no progress).

  The model is not asked to notice that it is stuck. The harness counts.
  """

  RULE = "loop_guard"

  def __init__(self, max_repeats: int = 2):
    # The same action on an unchanged screen may be tried `max_repeats` times.
    self.max_repeats = max_repeats
    self.blocks = 0
    self._last_key: Optional[tuple[str, str]] = None
    self._count = 0

  def reset(self) -> None:
    self.blocks = 0
    self._last_key = None
    self._count = 0

  def check(self, signature: str, screen_fingerprint: str) -> Verdict:
    key = (signature, screen_fingerprint)
    if key == self._last_key:
      self._count += 1
    else:
      self._last_key = key
      self._count = 1
    if self._count > self.max_repeats:
      self.blocks += 1
      return Verdict.block(
          self.RULE,
          "BLOCKED: you already tried exactly this action"
          f" {self.max_repeats} times on this same screen and nothing"
          " changed. Choose a different action.",
      )
    return Verdict.ok()

  @property
  def repeats(self) -> int:
    return self._count
