import time

from app.domain.game_clock import GameClock
from app.domain.color import Color



def test_initial_times_equal():
    clock = GameClock(300)
    assert clock.white_time == 300
    assert clock.black_time == 300


def test_initial_active_is_white():
    assert GameClock(300).active_color == Color.WHITE


def test_initial_not_running():
    assert GameClock(300).is_running is False


def test_increment_stored():
    clock = GameClock(300, increment_seconds=5)
    assert clock.increment == 5



def test_start_sets_running():
    clock = GameClock(300)
    clock.start()
    assert clock.is_running is True


def test_stop_sets_not_running():
    clock = GameClock(300)
    clock.start()
    clock.stop()
    assert clock.is_running is False


def test_start_twice_is_safe():
    clock = GameClock(300)
    clock.start()
    clock.start()
    assert clock.is_running is True



def test_active_player_time_decreases():
    clock = GameClock(300)
    clock.start()
    time.sleep(0.3)
    assert clock.get_time(Color.WHITE) < 300


def test_inactive_player_time_unchanged():
    clock = GameClock(300)
    clock.start()
    time.sleep(0.3)
    assert clock.get_time(Color.BLACK) == 300


def test_stopped_clock_time_frozen():
    clock = GameClock(300)
    clock.start()
    time.sleep(0.2)
    clock.stop()
    frozen = clock.get_time(Color.WHITE)
    time.sleep(0.2)
    assert clock.get_time(Color.WHITE) == frozen



def test_switch_changes_active():
    clock = GameClock(300)
    clock.start()
    clock.switch_turn()
    assert clock.active_color == Color.BLACK


def test_switch_back_to_white():
    clock = GameClock(300)
    clock.start()
    clock.switch_turn()
    clock.switch_turn()
    assert clock.active_color == Color.WHITE


def test_switch_applies_increment():
    clock = GameClock(300, increment_seconds=5)
    clock.start()
    clock.switch_turn()
    assert clock.white_time > 304


def test_switch_deducts_elapsed():
    clock = GameClock(300)
    clock.start()
    time.sleep(0.3)
    clock.switch_turn()
    assert clock.white_time < 300



def test_time_not_up_initially():
    clock = GameClock(300)
    clock.start()
    assert clock.is_time_up() is False


def test_time_up_after_running_out():
    clock = GameClock(1)
    clock.start()
    time.sleep(1.1)
    assert clock.is_time_up() is True


def test_time_up_checks_active_by_default():
    clock = GameClock(1)
    clock.start()
    time.sleep(1.1)
    assert clock.is_time_up() is True
    assert clock.is_time_up(Color.BLACK) is False



def test_tick_updates_active_time():
    clock = GameClock(300)
    clock.start()
    time.sleep(0.3)
    clock.tick()
    assert clock.white_time < 300