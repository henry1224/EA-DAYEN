"""Self-check for rules/signal_filter.py. Run from repo root: python3 -m rules.test_signal_filter"""
from .signal_filter import filter_signal

def test_direction_maps_to_action_with_no_quiet_hours():
    assert filter_signal("UP", "2026.10.16 10:00:00") == "BUY"
    assert filter_signal("DOWN", "2026.10.16 10:00:00") == "SELL"
    assert filter_signal("SIDEWAYS", "2026.10.16 10:00:00") == "WAIT"

def test_quiet_hours_forces_wait_even_on_up_signal():
    assert filter_signal("UP", "2026.10.16 03:00:00", quiet_hours=((0, 7),)) == "WAIT"

def test_quiet_hours_boundary_is_half_open():
    assert filter_signal("UP", "2026.10.16 07:00:00", quiet_hours=((0, 7),)) == "BUY"  # end excluded
    assert filter_signal("UP", "2026.10.16 06:59:59", quiet_hours=((0, 7),)) == "WAIT"  # just inside

def test_outside_quiet_hours_passes_through():
    assert filter_signal("DOWN", "2026.10.16 12:00:00", quiet_hours=((0, 7),)) == "SELL"

def test_unknown_direction_rejected():
    try:
        filter_signal("SOMETHING_ELSE", "2026.10.16 10:00:00")
        raise AssertionError("should reject unknown direction")
    except ValueError:
        pass

if __name__ == "__main__":
    test_direction_maps_to_action_with_no_quiet_hours()
    test_quiet_hours_forces_wait_even_on_up_signal()
    test_quiet_hours_boundary_is_half_open()
    test_outside_quiet_hours_passes_through()
    test_unknown_direction_rejected()
    print("OK — rules/signal_filter.py self-checks passed")
