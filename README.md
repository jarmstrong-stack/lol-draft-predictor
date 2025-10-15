# LoL Draft Predictor (composition-only)

1. Install dependencies:
   pip install -r requirements.txt

2. Add RIOT_API_KEY environment variable:
   export RIOT_API_KEY="RGAPI-XXXX"

3. Ingest Challenger/Grandmaster matches (may take hours depending on your limits):
   python scripts/ingest_matches.py

4. Convert raw JSONs to base CSV:
   python scripts/convert_raw_to_csv.py

5. Prepare Worlds CSV:
   - Put a CSV at examples/worlds_matches.csv with columns:
     match_id, patch, blue_champs (json list), red_champs (json list), winner

6. Build champion index:
   python scripts/build_champion_index.py

7. Train base Random Forest:
   python src/train_base.py

8. (Optional) Train embedding NN:
   python src/train_embed.py

9. Fine-tune on Worlds matches (after adding Worlds CSV):
   python src/fine_tune.py

10. Predict:
   python src/inference.py

