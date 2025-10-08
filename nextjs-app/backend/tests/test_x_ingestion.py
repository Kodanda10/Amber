from unittest.mock import patch, MagicMock
import pytest

from backend import x_client

def test_x_client_initialization():
    """Test that the XClient can be initialized."""
    with patch('tweepy.Client') as mock_tweepy_client:
        client = x_client.XClient(bearer_token="test_token")
        assert client is not None
        mock_tweepy_client.assert_called_once_with("test_token")

@patch('tweepy.Client', autospec=True)
def test_fetch_posts_for_leader(mock_tweepy_client):
    """Test fetching posts for a leader from X."""
    mock_tweepy_instance = mock_tweepy_client.return_value
    mock_user = MagicMock()
    mock_user.id = "12345"
    mock_tweepy_instance.get_user.return_value.data = mock_user
    mock_tweet = MagicMock()
    mock_tweet.text = "This is a tweet"
    mock_tweepy_instance.get_users_tweets.return_value.data = [mock_tweet]

    client = x_client.XClient(bearer_token="test_token")
    posts = client.fetch_posts("dummy_leader")

    assert posts is not None
    assert len(posts) == 1
    assert posts[0]["text"] == "This is a tweet"
    mock_tweepy_instance.get_user.assert_called_once_with(username="dummy_leader")
    mock_tweepy_instance.get_users_tweets.assert_called_once_with(id="12345")
