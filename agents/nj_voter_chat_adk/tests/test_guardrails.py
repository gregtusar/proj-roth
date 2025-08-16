from agents.nj_voter_chat_adk.policy import is_select_only, tables_within_allowlist
from agents.nj_voter_chat_adk.config import ALLOWED_TABLES

def test_select_only_positive():
    assert is_select_only("SELECT * FROM `proj-roth.voter_data.voters` LIMIT 1")

def test_select_only_negative():
    assert not is_select_only("DROP TABLE `proj-roth.voter_data.voters`")

def test_allowlist_ok():
    ok, illegal = tables_within_allowlist("SELECT * FROM proj-roth.voter_data.street_party_summary", ALLOWED_TABLES)
    assert ok and not illegal

def test_allowlist_block():
    ok, illegal = tables_within_allowlist("SELECT * FROM otherproj.otherds.other", ALLOWED_TABLES)
    assert not ok and illegal
