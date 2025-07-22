import pytest

from app.users.service import UsersService


@pytest.mark.parametrize(
    "user_id, email, exists",
    [
        (1, "fedor@moloko.ru", True),
        (2, "sharik@moloko.ru", True),
        (3, "test@test.com", True),
        (4, "wrong@person.com", False),
    ],
)
async def test_find_user_by_id(user_id, email, exists):
    user = await UsersService.find_by_id(user_id)

    if exists:
        assert user
        assert user.id == user_id
        assert user.email == email
    else:
        assert not user
