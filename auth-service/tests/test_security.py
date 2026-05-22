import pytest
from core.security import decode_access_token, hash_password, verify_password, hash_refresh_token, verify_refresh_token, generate_refresh_token

class TestSecurity:

    @pytest.mark.parametrize("input_pass", ["pass1", "pashard@123*"])
    async def test_hash_verify(self, input_pass: str):
        hash_1 = await hash_password(input_pass)
        
        assert await verify_password(input_pass, hash_1)
    
    async def test_wrong_password(self):
        hash_correct = await hash_password("correct")
        assert not await verify_password("wrong", hash_correct)

    def test_decode_valid_token(self):
        from core.security import create_access_token, decode_access_token
        token = create_access_token(subject="test", user_id=1)
        decoded = decode_access_token(token)
        assert decoded.sub == "test"
        assert decoded.user_id == 1

    def test_decode_expired_token(self):
        from core.security import create_access_token, decode_access_token
        from datetime import timedelta
        token = create_access_token(subject="test", user_id=1, expires_delta=timedelta(seconds=-1))
        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_invalid_token(self):
        decoded = decode_access_token("invalidtoken")
        assert decoded is None

    def test_refresh_flow(self):
        refresh_token = generate_refresh_token()
        hashed_refresh_token = hash_refresh_token(refresh_token)
        assert verify_refresh_token(refresh_token, hashed_refresh_token)
    
    def test_wrong_refresh_token(self):
        refresh_token = generate_refresh_token()
        hashed_refresh_token = hash_refresh_token(refresh_token)
        assert not verify_refresh_token("wrongtoken", hashed_refresh_token)