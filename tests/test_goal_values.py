"""V4 goal-value tracker: extraction from real AndroidWorld goals."""

from gui_agent import goal_values

CONTACT = "Create a new contact for Isla Martin. Their number is +15256606183."
NOTE = ("Create a new note in Markor named 2023_01_26_wise_yacht.md with the"
        " following text: Ignorance is bliss.")
NOTE_SMS = ("Create a new note in Markor named fair_ant_XOdi.txt with the"
            " following text: Actions speak louder than words.. Share the entire"
            " content of the note with the phone number +13192815309 via SMS"
            " using Simple SMS Messenger")


def _shape(goal):
  return [(v.kind, v.label, v.parts) for v in goal_values.extract(goal)]


def test_contact_goal_tracks_each_name_part_and_the_number():
  assert _shape(CONTACT) == [
      ("name", "Isla Martin", ("Isla", "Martin")),
      ("phone", "+15256606183", ("+15256606183",)),
  ]


def test_note_goal_tracks_file_name_and_text_but_not_the_extension():
  assert _shape(NOTE) == [
      ("file", "2023_01_26_wise_yacht.md", ("2023_01_26_wise_yacht",)),
      ("text", "Ignorance is bliss.", ("Ignorance is bliss.",)),
  ]


def test_note_and_sms_goal_stops_the_text_before_the_next_instruction():
  shapes = _shape(NOTE_SMS)
  assert ("text", "Actions speak louder than words.",
          ("Actions speak louder than words.",)) in shapes
  assert ("phone", "+13192815309", ("+13192815309",)) in shapes
  # App names are not values.
  assert not any("Messenger" in label for _, label, _ in shapes)


def test_the_omitted_surname_is_reported_as_missing():
  tracker = goal_values.GoalTracker(CONTACT)
  assert tracker.missing_parts(["Isla", "+15256606183"]) == ["Martin"]
  assert tracker.missing_parts(["Isla Martin", "+1 525 660 6183"]) == []
  text = tracker.render(["Isla"])
  assert '"Isla Martin": still missing "Martin"' in text
  assert '"+15256606183": NOT typed yet' in text


def test_typed_matching_ignores_case_and_a_trailing_full_stop():
  tracker = goal_values.GoalTracker(NOTE)
  assert tracker.missing_parts(["2023_01_26_wise_yacht", "ignorance is bliss"]) == []
  assert tracker.missing_parts(["2023_01_26_wise_yacht.md"]) == ["Ignorance is bliss."]


def test_goal_without_literal_values_tracks_nothing():
  tracker = goal_values.GoalTracker("Turn on wifi.")
  assert tracker.values == []
  assert tracker.render([]) == ""
