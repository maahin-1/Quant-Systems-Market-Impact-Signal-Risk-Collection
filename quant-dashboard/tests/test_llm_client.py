import pytest
from unittest.mock import patch, MagicMock


def _resp(status: int, content: str = "", text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    return resp


@patch("llm.client.requests.post", return_value=_resp(200, "Test LLM response"))
def test_query_llm_returns_response_text(mock_post):
    from llm.client import query_llm
    result = query_llm("Test prompt")
    assert result.startswith("[via ")
    assert result.endswith("Test LLM response")


@patch("llm.client.requests.post", return_value=_resp(200, "ok"))
def test_query_llm_sends_correct_model(mock_post):
    from llm.client import query_llm
    query_llm("prompt", model="openai/gpt-4o")
    payload = mock_post.call_args_list[0][1]["json"]
    assert payload["model"] == "openai/gpt-4o"


@patch("llm.client.requests.post", return_value=_resp(200, "ok"))
def test_query_llm_sends_prompt_as_user_message(mock_post):
    from llm.client import query_llm
    query_llm("Hello LLM")
    payload = mock_post.call_args[1]["json"]
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"] == "Hello LLM"


@patch("llm.client.time.sleep")
@patch("llm.client.requests.post")
def test_query_llm_falls_back_when_rate_limited(mock_post, mock_sleep):
    from llm.client import query_llm
    mock_post.side_effect = [_resp(429), _resp(200, "from fallback")]
    result = query_llm("prompt")
    assert "from fallback" in result
    assert mock_post.call_count == 2
    first = mock_post.call_args_list[0][1]["json"]["model"]
    second = mock_post.call_args_list[1][1]["json"]["model"]
    assert first != second


@patch("llm.client.requests.post", return_value=_resp(401, text="Unauthorized"))
def test_query_llm_raises_when_all_models_fail(mock_post):
    from llm.client import query_llm
    with pytest.raises(RuntimeError, match="All free models failed"):
        query_llm("prompt")
    from llm.client import _FALLBACK_MODELS
    assert mock_post.call_count == len(set(_FALLBACK_MODELS))
