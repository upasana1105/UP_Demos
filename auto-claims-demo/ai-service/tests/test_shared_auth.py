from unittest.mock import patch, MagicMock

def test_google_auth():
    from shared_auth import GoogleAuth
    auth = GoogleAuth()

    with patch('google.auth.default') as mock_default:
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.token = "fake_token"
        mock_default.return_value = (mock_creds, "project")

        headers = auth._get_token()
        assert headers["Authorization"] == "Bearer fake_token"

        # Test auth_flow generator
        mock_req = MagicMock()
        mock_req.headers = {}
        gen = auth.auth_flow(mock_req)

        # first yield
        yielded_req = next(gen)
        assert yielded_req.headers["Authorization"] == "Bearer fake_token"

        # Mocking 401 response and handling Send next step
        mock_res = MagicMock()
        mock_res.status_code = 401

        try:
            next_req = gen.send(mock_res)
            assert next_req is not None
        except StopIteration:
            pass
