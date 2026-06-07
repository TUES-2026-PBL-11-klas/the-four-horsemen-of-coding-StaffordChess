from app.domain.color import Color



def test_white_opposite_is_black():
    assert Color.WHITE.get_opposite_color() == Color.BLACK


def test_black_opposite_is_white():
    assert Color.BLACK.get_opposite_color() == Color.WHITE


def test_opposite_is_symmetric():
    assert Color.WHITE.get_opposite_color().get_opposite_color() == Color.WHITE
    assert Color.BLACK.get_opposite_color().get_opposite_color() == Color.BLACK



def test_white_pawn_direction_is_negative():
    assert Color.WHITE.get_pawn_direction() == -1


def test_black_pawn_direction_is_positive():
    assert Color.BLACK.get_pawn_direction() == 1


def test_pawn_directions_are_opposite():
    assert Color.WHITE.get_pawn_direction() == -Color.BLACK.get_pawn_direction()



def test_color_values():
    assert Color.WHITE.value == "white"
    assert Color.BLACK.value == "black"


def test_only_two_colors():
    assert len(list(Color)) == 2