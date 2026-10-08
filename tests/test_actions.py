"""Parsing, validation and grounding."""

import pytest

from gui_agent import actions
from gui_agent import observation
from tests import fakes


def _views():
  elements = [
      fakes.el("Contacts", (0, 100, 1080, 200)),
      fakes.el("Save", (800, 300, 1000, 400), cls="android.widget.Button", clickable=True),
      fakes.el("", (100, 500, 980, 620), hint="First name", cls="android.widget.EditText", editable=True),
      fakes.el("", (0, 700, 1080, 2300), cls="androidx.recyclerview.widget.RecyclerView", scrollable=True),
  ]
  return observation.build_views(elements, fakes.SCREEN)


# --- parsing: the format drift cases from the lecture ------------------------


@pytest.mark.parametrize(
    "raw",
    [
        '{"thought": "tap save", "action_type": "click", "index": 1}',
        'Sure! Here is the result:\n{"thought": "x", "action_type": "click", "index": 1}',
        '```json\n{"thought": "x", "action_type": "click", "index": 1}\n```',
        '<think>hmm { not json }</think>{"action_type": "click", "index": "1"}',
        "{'thought': 'single quotes', 'action_type': 'click', 'index': 1}",
        '{"action": "tap", "index": 1.0}',
    ],
)
def test_parse_tolerates_format_drift(raw):
  action = actions.parse_action(raw, "index")
  assert action.action_type == "click"
  assert action.index == 1


def test_parse_keeps_braces_inside_strings():
  raw = '{"thought": "the field says {name}", "action_type": "input_text", "index": 2, "text": "a}b{c"}'
  action = actions.parse_action(raw, "index")
  assert action.text == "a}b{c"


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "I will tap the save button.",
        '{"thought": "no type"}',
        '{"action_type": "fly"}',
        '{"action_type": "click"}',
        '{"action_type": "click", "x": 5, "y": 5}',  # coordinates in index mode
        '{"action_type": "input_text", "index": 2, "text": ""}',
        '{"action_type": "scroll", "direction": "sideways"}',
        '{"action_type": "open_app"}',
        '{"action_type": "click", "index": true}',
    ],
)
def test_parse_rejects_invalid_replies(raw):
  with pytest.raises(actions.ActionError):
    actions.parse_action(raw, "index")


def test_irrelevant_fields_from_constrained_decoding_are_ignored():
  raw = '{"thought": "done", "action_type": "status", "index": 0, "text": "", "goal_status": "complete"}'
  action = actions.parse_action(raw, "index")
  assert action.action_type == "status"
  assert action.goal_status == "complete"
  assert action.index is None and action.text is None


def test_done_aliases_and_swipe_direction():
  assert actions.parse_action('{"action_type": "done"}', "index").goal_status == "complete"
  assert actions.parse_action('{"action_type": "infeasible"}', "index").goal_status == "infeasible"
  # A finger swipe up reveals content further down = scroll down.
  assert actions.parse_action('{"action_type": "swipe", "direction": "up"}', "index").direction == "down"


# --- grounding ---------------------------------------------------------------


def test_index_grounding_is_a_table_lookup():
  action = actions.parse_action('{"action_type": "click", "index": 1}', "index")
  resolved = actions.resolve_action(action, _views(), fakes.SCREEN, "index")
  assert resolved.tap_xy == (900, 350)  # centre of the Save button
  assert resolved.env_action == {"action_type": "click", "x": 900, "y": 350}
  assert resolved.target.text == "Save"
  assert "Save" in resolved.description


def test_unknown_index_is_an_error_for_the_model_not_a_crash():
  action = actions.parse_action('{"action_type": "click", "index": 99}', "index")
  with pytest.raises(actions.ActionError, match="no element"):
    actions.resolve_action(action, _views(), fakes.SCREEN, "index")


def test_relative_coordinates_are_scaled_to_screen_pixels():
  action = actions.parse_action('{"action_type": "click", "x": 500, "y": 250}', "coordinate")
  resolved = actions.resolve_action(action, _views(), fakes.SCREEN, "coordinate")
  assert resolved.tap_xy == (540, 600)
  assert resolved.env_action == {"action_type": "click", "x": 540, "y": 600}
  # Hit-testing tells us what the pixel tap actually landed on.
  assert resolved.target is not None and resolved.target.hint == "First name"


def test_image_pixel_coordinates_are_scaled_by_the_image_size():
  action = actions.parse_action('{"action_type": "click", "x": 230, "y": 512}', "coordinate")
  resolved = actions.resolve_action(
      action, _views(), fakes.SCREEN, "coordinate", "image_pixels", (460, 1024)
  )
  assert resolved.tap_xy == (540, 1200)


def test_out_of_range_coordinates_are_rejected():
  action = actions.parse_action('{"action_type": "click", "x": 1500, "y": 10}', "coordinate")
  with pytest.raises(actions.ActionError, match="out of range"):
    actions.resolve_action(action, _views(), fakes.SCREEN, "coordinate")


def test_edge_coordinates_stay_on_screen():
  assert actions.scale_point(1000, 1000, fakes.SCREEN, "relative_1000") == (1079, 2399)
  assert actions.scale_point(0, 0, fakes.SCREEN, "relative_1000") == (0, 0)


def test_input_text_carries_text_and_tap_point():
  action = actions.parse_action(
      '{"action_type": "input_text", "index": 2, "text": "Nikola"}', "index"
  )
  resolved = actions.resolve_action(action, _views(), fakes.SCREEN, "index")
  assert resolved.env_action == {
      "action_type": "input_text", "text": "Nikola", "x": 540, "y": 560,
  }


def test_scroll_only_targets_scrollable_elements():
  views = _views()
  inside_list = actions.resolve_action(
      actions.parse_action('{"action_type": "scroll", "direction": "down", "index": 3}', "index"),
      views, fakes.SCREEN, "index",
  )
  assert inside_list.env_action == {"action_type": "scroll", "direction": "down", "index": 3}
  on_button = actions.resolve_action(
      actions.parse_action('{"action_type": "scroll", "direction": "down", "index": 1}', "index"),
      views, fakes.SCREEN, "index",
  )
  assert on_button.env_action == {"action_type": "scroll", "direction": "down"}


def test_schema_only_offers_allowed_apps_and_known_actions():
  schema = actions.action_schema("index", ("markor", "clock"), with_note=True)
  assert schema["properties"]["app_name"]["enum"] == ["markor", "clock"]
  assert set(schema["properties"]["action_type"]["enum"]) == set(actions.ACTION_TYPES)
  assert "index" in schema["properties"] and "x" not in schema["properties"]
  assert list(schema["properties"])[0] == "thought"  # reasoning before the action
  coordinate = actions.action_schema("coordinate", ("markor",), with_note=False)
  assert "x" in coordinate["properties"] and "index" not in coordinate["properties"]
