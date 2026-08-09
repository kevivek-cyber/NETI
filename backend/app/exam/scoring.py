import json
from app.api.ceremony_router import ceremony_manager
from app.exam.seeds import derive_seed
from app.generation.generator import generate, load_bank
from app.db.connection import get_db
from app.generation.blueprint import DEMO

async def compute_score(candidate_pseudonym: str, session_id: str) -> dict:
    if not ceremony_manager.answer_key:
        raise ValueError("Answer key not released. The window close ceremony must be completed first.")
        
    async for conn in get_db():
        row = await conn.fetchrow(
            "SELECT responses FROM submission_receipts WHERE candidate_pseudonym = $1 AND session_id = $2",
            candidate_pseudonym, session_id
        )
        if not row:
            raise ValueError(f"No submission found for candidate {candidate_pseudonym} in session {session_id}")
            
    responses = json.loads(row["responses"])
    
    seed = derive_seed(
        master_seed=ceremony_manager.master_seed,
        session_id=session_id,
        pseudonym_hex=candidate_pseudonym
    )
    
    paper = generate(
        seed=seed,
        bank=load_bank(),
        blueprint=DEMO,
        bank_key=ceremony_manager.bank_key,
        answer_key=ceremony_manager.answer_key
    )
    
    # map item_id to answer_index
    correct_answers = {q["item_id"]: q["answer_index"] for q in paper["questions"]}
    
    # get final selected option per question
    final_responses = {}
    for event in responses:
        final_responses[event["question_id"]] = event["selected_option_index"]
        
    score = 0
    correct = 0
    incorrect = 0
    omitted = 0
    
    for item_id, correct_idx in correct_answers.items():
        ans = final_responses.get(item_id, -1)
        if ans == correct_idx:
            score += 4
            correct += 1
        elif ans == -1:
            omitted += 1
        else:
            score -= 1
            incorrect += 1
            
    return {
        "score": score,
        "correct": correct,
        "incorrect": incorrect,
        "omitted": omitted
    }
