from intelligence import deterministic_gate,similarity,duplicate

def test_rejects_generic_linkedin_opening():
 assert deterministic_gate("Absolutely, this is so important.")[0] is False

def test_rejects_engagement_bait():
 assert deterministic_gate("A useful observation. Thoughts?")[0] is False

def test_accepts_plain_specific_language():
 assert deterministic_gate("Teams can hide a failing process by compensating locally until the system runs out of slack.")[0] is True

def test_similarity_detects_echo():
 assert similarity("AI code can hide intent and provenance","AI-generated code can hide intent and provenance") > .5

def test_duplicate_memory():
 posts=[{"text":"Technical debt becomes expensive when teams cannot explain why the system behaves as it does."}]
 assert duplicate("Technical debt becomes expensive when teams cannot explain why the system behaves as it does.",posts)
