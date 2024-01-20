from tests.api import add_fixtures
from tests.data.user import color_valid, user
from tests.data.user import color_not_valid
from app.validation import color_valid as valid_func, length_password_valid, user_same_name_valid


def test_color_valid():
    valid_colors = color_valid()
    not_valid_colors = color_not_valid()
    for color in valid_colors:
        assert bool(valid_func(color)) is True
    for color in not_valid_colors:
        assert bool(valid_func(color)) is False


def test_length_password():
    password = ''
    for i in range(1, 6):
        password += str(i)
        assert length_password_valid(password) is True
    password = '123456'
    assert length_password_valid(password) is False


