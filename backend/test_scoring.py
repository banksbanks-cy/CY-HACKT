from app.services.scoring_service import compute_score

text = "Critical zero-day vulnerability actively exploited in ransomware attack"

print(compute_score(text))
